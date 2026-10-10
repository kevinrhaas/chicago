"""Glessner's reconstructed roof-edge stock, on the existing roof geometry.

The record owns dimensions. Taylor 2135 and the HABS elevations bound the
repeated silhouette; hidden stock and flashing sections are reconstructed.
All additions use raw faces: neither ridge ornaments nor metal become tiles.
"""
from __future__ import annotations

import math


def _sub(a, b): return tuple(x-y for x,y in zip(a,b))
def _dot(a, b): return sum(x*y for x,y in zip(a,b))
def _mix(a, b, t): return tuple(x+(y-x)*t for x,y in zip(a,b))
def _unit(a):
    n=math.sqrt(_dot(a,a))
    return tuple(x/n for x in a) if n>1e-12 else (0.,0.,0.)


def _solid(b, front, back, mat, confidence=1., skip_sides=(), ends=(True,True)):
    """Closed prism, including both end faces and a real underside."""
    from archetypes.masonry_house import _normal
    forward=_sub(back[0],front[0])
    reverse=_dot(_normal(front),forward)>0
    faces=([list(reversed(front)) if reverse else front] if ends[0] else [])
    faces+=([back if reverse else list(reversed(back))] if ends[1] else [])
    sides=[[front[i],back[i],back[(i+1)%len(front)],front[(i+1)%len(front)]]
              for i in range(len(front)) if i not in skip_sides]
    faces += [list(reversed(face)) if reverse else face for face in sides]
    for face in faces:b.raw(face,confidence,mat)


def _receipt(b, kind, **values):
    if not hasattr(b,'roof_edge_details'): b.roof_edge_details=[]
    b.roof_edge_details.append({'kind':kind,**values})


def _ridge_point(r, along, across, height):
    offset=along-r.get('ridge_origin',0)
    at=r['ridge_at']+r.get('ridge_skew',0)*offset+across
    z=r['ridge_z']+r.get('ridge_slope',0)*offset+height
    return (at,along,z) if r['axis']=='y' else (along,at,z)


def _ridge_intervals(params,r,lo,hi,radius):
    """Do not run closed cap stock through a chimney or the stable cupola."""
    intervals=[(lo,hi)]
    obstacles=list(params.chimneys)+[
        {**t,'z1':t['top_z']} for t in params.turrets]
    for c in obstacles:
        if c['z1']<r['ridge_z']+.025: continue
        ca,cb=(c['x0'],c['x1']) if r['axis']=='y' else (c['y0'],c['y1'])
        if not ca-radius<r['ridge_at']<cb+radius: continue
        a,z=(c['y0'],c['y1']) if r['axis']=='y' else (c['x0'],c['x1'])
        a-=.012;z+=.012
        intervals=[part for left,right in intervals for part in
                   ((left,min(right,a)),(max(left,z),right)) if part[1]-part[0]>.025]
    return intervals


def ridge_chain(b,params,r,lo,hi,*,join_end=False):
    s=params.detail['roof_edges'];radius=s['cap_radius_m'];seat=s['cap_seat_m']
    step=s['ridge_spacing_ft']*.3048;rise=s['crest_rise_m'];width=s['crest_width_m']
    reduced=getattr(b,'reduced_roof_details',False);segments=4 if reduced else 12
    angles=[math.pi*j/segments for j in range(segments+1)]
    def section(along,crest=False):
        points=[]
        for a in angles:
            rad=radius+(rise*math.sin(a)**2 if crest else 0)
            points.append(_ridge_point(r,along,rad*math.cos(a),seat+rad*math.sin(a)))
        # The hidden base crosses the host ridge. A positive floor would
        # leave the entire closed barrel floating above the tiled roof.
        return points+[_ridge_point(r,along,-radius*.5,seat-radius*math.sqrt(3)/2),
                       _ridge_point(r,along,radius*.5,seat-radius*math.sqrt(3)/2)]
    for start,end in _ridge_intervals(params,r,lo,hi,radius):
        if reduced:
            _solid(b,section(start),section(end),19)
        count=0
        for i in range(math.floor((start-lo)/step),math.ceil((end-lo)/step)):
            a=max(start,lo+i*step);z=min(end,lo+(i+1)*step+s['cap_overlap_m'])
            if z-a<.015:continue
            if not reduced:_solid(b,section(a),section(z),19+i%3)
            # Short cut pieces at abutments never sprout an extra terminal tooth.
            centre=lo+(i+.16)*step
            if centre-width/2<start+.01 or centre+width/2>end-.01:continue
            if join_end and centre>hi-radius-.08:continue
            # These three underside faces are buried inside the opaque barrel;
            # the assembled moulding stays closed without duplicate hidden stock.
            _solid(b,section(centre-width/2,True),section(centre+width/2,True),19+i%3,
                   skip_sides=(segments,segments+1,segments+2))
            count+=1
        _receipt(b,'ridge',axis=r['axis'],at=r['ridge_at'],z=r['ridge_z'],
                 start=start,end=end,collars=count,spacing_m=step,radius_m=radius,
                 crest_rise_m=rise,crest_width_m=width)


def add_ridges(b,params):
    from archetypes.masonry_house_v4_west_roof import ridge_ranges
    for source in params.ranges:
        for r,lo,hi in ridge_ranges(source):
            # The west cross-gable finishes at the continuous north-south ridge.
            join=r['axis']=='x' and source.get('stable_roof') and abs(hi-source['ridge_at'])<.02
            if join:hi-=params.detail['roof_edges']['cap_radius_m']
            ridge_chain(b,params,r,lo,hi,join_end=join)


def finial(b,x,y,z,height,mat):
    """Moulded seat, neck and tapered terminal inside the inherited height."""
    if height<=0:return
    segments=8 if getattr(b,'reduced_roof_details',False) else 16
    # Existing finials were a 120mm square post and a 264mm-wide six-sided cone.
    # Keep the maximum radius and apex, while giving their base a seated profile.
    profile=[(-.03,.105),(0,.132),(.12*height,.122),(.20*height,.066),
             (.53*height,.055),(.64*height,.085),(.82*height,.055),(height,0.)]
    rings=[[(x+r*math.cos(2*math.pi*i/segments),y+r*math.sin(2*math.pi*i/segments),z+h)
            for i in range(segments)] for h,r in profile]
    for a,c in zip(rings,rings[1:]):
        for i in range(segments):
            j=(i+1)%segments
            face=[a[i],a[j],c[j]] if math.dist(c[i],c[j])<1e-9 else [a[i],a[j],c[j],c[i]]
            mid=tuple(sum(p[k] for p in face)/len(face) for k in range(3))
            b.raw(face,1.,mat,(mid[0]-x,mid[1]-y,0.))
    b.raw(rings[0],1.,mat,(0,0,-1))
    _receipt(b,'finial',centre=[x,y,z],height_m=height,max_radius_m=.132)


def hip_caps(b,p,q):
    """Solid overlapping covers, with the inherited 47mm hip radius."""
    tangent=_unit(_sub(q,p));across=_unit((tangent[1],-tangent[0],0))
    outward=(across[1]*tangent[2]-across[2]*tangent[1],
             across[2]*tangent[0]-across[0]*tangent[2],
             across[0]*tangent[1]-across[1]*tangent[0])
    length=math.dist(p,q);count=max(1,math.ceil(length/.27));radius=.047
    segments=2 if getattr(b,'reduced_roof_details',False) else 8
    def section(t):
        profile=[(radius*math.cos(math.pi*j/segments),.009+radius*math.sin(math.pi*j/segments))
                 for j in range(segments+1)]+[(-radius,-.009),(radius,-.009)]
        return [tuple(p[k]+(q[k]-p[k])*t+across[k]*a+outward[k]*z for k in range(3)) for a,z in profile]
    for i in range(count):
        a=i/count+.002/length;z=min(1,(i+1)/count+.014/length)
        _solid(b,section(a),section(z),19+i%3)
    _receipt(b,'hip',start=p,end=q,caps=count,radius_m=radius)


def _edges(surfaces):
    """Split collinear T junctions before identifying actual shared roof edges."""
    points={tuple(round(v,7) for v in p) for s in surfaces for p in s['points']}
    edges={}
    for index,s in enumerate(surfaces):
        polygon=s['points']
        for p,q in zip(polygon,polygon[1:]+polygon[:1]):
            direction=_sub(q,p);length2=_dot(direction,direction)
            if length2<1e-12:continue
            cuts=[0.,1.]
            for v in points:
                t=_dot(_sub(v,p),direction)/length2
                if 1e-7<t<1-1e-7 and math.dist(v,_mix(p,q,t))<2e-6:cuts.append(t)
            cuts=sorted(set(round(t,9) for t in cuts))
            for a,c in zip(cuts,cuts[1:]):
                v,w=_mix(p,q,a),_mix(p,q,c)
                key=tuple(sorted(tuple(round(x,6) for x in pt) for pt in (v,w)))
                edges.setdefault(key,[]).append((index,v,w))
    return edges


def add_edges(b,params):
    """Close exposed eave skins and dress true concave, sloping intersections."""
    from archetypes.masonry_house_v4_detail import area,clip
    s=params.detail['roof_edges'];surfaces=list(b.roof_surfaces)
    edges=_edges(surfaces)
    eaves={};corners={}
    def key(p):return tuple(round(v,6) for v in p)
    for members in edges.values():
        if len(members)!=1:continue
        i,p,q=members[0];tangent=_unit(_sub(q,p))
        outward=_unit((tangent[1],-tangent[0],0))
        if math.dist(p,q)<.10 or abs(p[2]-q[2])>.003 or _dot(outward,surfaces[i]['normal'])<.1:continue
        eaves[(i,key(p),key(q))]=outward
        for v in (p,q):corners.setdefault(key(v),[]).append(outward)
    for members in edges.values():
        i,p,q=members[0];length=math.dist(p,q)
        if length<.10:continue
        host=surfaces[i];n=host['normal'];tangent=_unit(_sub(q,p))
        if len(members)==1:
            if abs(p[2]-q[2])>.003:continue
            outward=eaves.get((i,key(p),key(q)))
            if outward is None:continue
            depth=s['eave_fascia_depth_m'];lip=s['eave_lip_depth_m']
            # Exact upper roof edge retained; a closed fascia fills the old gap
            # between its top and underside. A narrow lower step makes a soffit.
            def section(v):
                directions=corners[key(v)];offset=outward
                if len(directions)==2 and _dot(*directions)>-.95:
                    # Adjacent lengths share the exact mitred inner corner.
                    den=1+_dot(*directions)
                    offset=tuple((directions[0][k]+directions[1][k])/den for k in range(3))
                return [v,(v[0],v[1],v[2]-depth),
                        (v[0]-offset[0]*.065,v[1]-offset[1]*.065,v[2]-depth),
                        (v[0]-offset[0]*.065,v[1]-offset[1]*.065,v[2]-lip)]
            _solid(b,section(p),section(q),23,
                   ends=(len(corners[key(p)])!=2,len(corners[key(q)])!=2))
            _receipt(b,'eave',start=p,end=q,depth_m=depth)
        elif len(members)==2:
            j=members[1][0];other=surfaces[j];m=other['normal']
            if i==j or _dot(n,m)>.96 or abs(p[2]-q[2])<.03:continue
            centre=tuple(sum(v[k] for v in other['points'])/len(other['points']) for k in range(3))
            if _dot(n,_sub(centre,p))<1e-5:continue  # convex hip/ridge, not valley
            for surface in (host,other):
                centre=tuple(sum(v[k] for v in surface['points'])/len(surface['points']) for k in range(3))
                side=_sub(centre,p);side=_sub(side,tuple(_dot(side,tangent)*x for x in tangent));side=_unit(side)
                width=s['valley_width_m']/2;stock=s['flashing_stock_m']
                top=[(v[0],v[1],v[2]+.010) for v in
                     [p,q,tuple(q[k]+side[k]*width for k in range(3)),tuple(p[k]+side[k]*width for k in range(3))]]
                outline=surface['points']
                if area(outline)<0:outline=list(reversed(outline))
                for a,c in zip(outline,outline[1:]+outline[:1]):top=clip(top,a,c)
                if len(top)<3 or abs(area(top))<1e-8:continue
                _solid(b,top,[(x,y,z-stock) for x,y,z in top],4)
            _receipt(b,'valley',start=p,end=q,width_m=s['valley_width_m'])
    add_abutments(b,params,surfaces)


def add_abutments(b,params,surfaces):
    """Folded apron/upstand follows the actual roof at each chimney wall."""
    from archetypes.masonry_house_v4_detail import area
    def roof(x,y):
        highest=None
        for s in surfaces:
            polygon=s['points'];sign=1 if area(polygon)>0 else -1
            if any(sign*((q[0]-p[0])*(y-p[1])-(q[1]-p[1])*(x-p[0])) < -1e-6
                   for p,q in zip(polygon,polygon[1:]+polygon[:1])):continue
            n=s['normal'];p=polygon[0]
            z=p[2]-(n[0]*(x-p[0])+n[1]*(y-p[1]))/n[2]
            if highest is None or z>highest[0]:highest=(z,n)
        return highest
    stock=params.detail['roof_edges']['flashing_stock_m']
    for c in params.chimneys:
        corners=[(c['x0'],c['y0']),(c['x1'],c['y0']),(c['x1'],c['y1']),(c['x0'],c['y1'])]
        for p,q in zip(corners,corners[1:]+corners[:1]):
            dx,dy=q[0]-p[0],q[1]-p[1];length=math.hypot(dx,dy);out=(dy/length,-dx/length)
            # One roof plane on either side of a ridge. Recursive subdivision
            # isolates a crossing to <=8mm, instead of bridging it with a quad.
            def sample(t):return roof(p[0]+dx*t+out[0]*.008,p[1]+dy*t+out[1]*.008)
            pieces=[]
            def split(a,z,depth=0):
                mid=(a+z)/2;aa,mm,zz=sample(a),sample(mid),sample(z)
                if aa is None or mm is None or zz is None:return
                if abs(mm[0]-(aa[0]+zz[0])/2)>.001 and depth<9:
                    split(a,mid,depth+1);split(mid,z,depth+1);return
                if c['z0']-.05<mm[0]<c['z1']-.12:pieces.append((a,z,aa,zz))
            split(0,1)
            for a,z,aa,zz in pieces:
                def section(t,hit):
                    x,y=p[0]+dx*t+out[0]*.006,p[1]+dy*t+out[1]*.006
                    height,n=hit;fall=-(n[0]*out[0]+n[1]*out[1])/n[2]
                    def P(offset,rise):return (x+out[0]*offset,y+out[1]*offset,height+rise)
                    return [P(0,.12),P(stock,.12),P(stock,.012),
                            P(.09,.012+.09*fall),P(.09,.012+.09*fall-stock),P(0,.012-stock)]
                _solid(b,section(a,aa),section(z,zz),4)
                _receipt(b,'abutment',chimney=c['name'],start=section(a,aa)[0],
                         end=section(z,zz)[0],height_m=.12,width_m=.09)
