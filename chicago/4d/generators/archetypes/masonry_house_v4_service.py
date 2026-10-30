"""T-2223: joined service rails, seated supports and a connected paired gate.

The retained HABS plan controls the layout. Stock, joints and capitals are
bounded reconstructions, separately recorded from the later stair excluded by
the phase register. Light keeps all interfaces; only shallow brick relief is
replaced by its existing metric brick material and normal map.
"""
from __future__ import annotations

import math
from archetypes.masonry_house_v4_finish import flat_brick,grain_members


def _box(b,lo,hi,conf,mat,skip=()):
    old=b.decorate
    try:
        b.decorate=False
        b.add_box(*lo,*hi,conf,mat,skip=skip)
    finally:
        b.decorate=old


def _brick_box(b,lo,hi,conf):
    from archetypes import masonry_house_v4_detail as d
    old=b.decorate
    try:
        b.decorate=not getattr(b,'reduced_service_access',False)
        d.legacy._box(b,*lo,*hi,conf,d.BRICK if b.decorate else flat_brick(b))
    finally:
        b.decorate=old


def _capital(b,x,y,bottom,width,shaft_width,height,bevel,conf):
    from archetypes import masonry_house_v4_detail as d
    def ring(w,z):
        h=w/2
        return [(x-h,y-h,z),(x+h,y-h,z),(x+h,y+h,z),(x-h,y+h,z)]
    levels=[ring(shaft_width,bottom),ring(width,bottom+bevel),ring(width,bottom+height)]
    for low,high in zip(levels,levels[1:]):
        for i in range(4):
            j=(i+1)%4
            b.raw([low[i],low[j],high[j],high[i]],conf,d.TRIM)
    # The bottom seats on the pier; the top is wholly beneath the landing slab.


def _rail(b,points,width,thickness,conf):
    """One continuous closed bar, with shared miter sections at every turn."""
    from archetypes import masonry_house_v4_detail as d
    sides=[]
    for a,q in zip(points,points[1:]):
        sides.append(d.norm((a[1]-q[1],q[0]-a[0],0)))
    rings=[]
    for i,p in enumerate(points):
        if i==0:n=sides[0];scale=width/2
        elif i==len(points)-1:n=sides[-1];scale=width/2
        else:
            n=d.norm(tuple(sides[i-1][k]+sides[i][k] for k in range(3)))
            scale=width/(2*d.dot(n,sides[i]))
        rings.append([(p[0]+n[0]*scale*u,p[1]+n[1]*scale*u,p[2]+thickness*v/2)
                      for u,v in ((-1,-1),(1,-1),(1,1),(-1,1))])
    for a,q,ra,rq in zip(points,points[1:],rings,rings[1:]):
        centre=tuple((a[k]+q[k])/2 for k in range(3))
        for i in range(4):
            j=(i+1)%4;face=[ra[i],rq[i],rq[j],ra[j]]
            want=tuple(sum(p[k] for p in face)/4-centre[k] for k in range(3))
            b.raw(face,conf,d.IRON,want)
    b.raw(rings[0],conf,d.IRON,d.sub(points[0],points[1]))
    b.raw(rings[-1],conf,d.IRON,d.sub(points[-1],points[-2]))
    if not hasattr(b,'service_rails'):b.service_rails=[]
    b.service_rails.append({'points':points,'width':width,'thickness':thickness,'closed_ends':True})


def build_stair(b,params):
    from archetypes import masonry_house_v4_detail as d
    s=params.detail['north_court_service_stair'];cfg=params.detail['service_access']
    spec=cfg['stair'];rail=cfg['rail'];conf=params.conf('service_access_details')
    x0,x1=s['landing_x'];y0,y1=s['landing_y'];z=s['landing_z']
    fx0,fx1=s['flight_x'];fy0,fy1=s['flight_y']
    count=s['steps'];run=(fy1-fy0)/count;rise=z/count
    thickness=spec['slab_thickness_m'];buried=spec['footing_bottom_m']
    _box(b,(x0,y0,z-thickness),(x1,y1,z),conf,d.TRIM)
    b.service_piers=[]
    for x in (x1-.23,(x0+x1)/2):
        y=y0+.19;w=spec['pier_width_m'];cap=spec['pier_cap_width_m']
        top=z-thickness-spec['pier_cap_height_m'];h=w/2
        _box(b,(x-cap/2,y-cap/2,buried),(x+cap/2,y+cap/2,spec['footing_top_m']),conf,d.TRIM,('bottom',))
        _brick_box(b,(x-h,y-h,spec['footing_top_m']),(x+h,y+h,top),conf)
        _capital(b,x,y,top,cap,w,spec['pier_cap_height_m'],spec['pier_cap_bevel_m'],conf)
        b.service_piers.append({'x':x,'y':y,'base':buried,'capital_base':top,'top':z-thickness,'width':w,'cap_width':cap})
    for i in range(count):
        a=fy0+run*i;c=a+run;top=rise*(i+1)
        _box(b,(fx0,a,buried),(fx1,c,top),conf,d.TRIM,('bottom','top'))
        _box(b,(fx0-spec['nosing_side_m'],a-spec['nosing_front_m'],top-spec['nosing_height_m']),
             (fx1+spec['nosing_side_m'],c,top),conf,d.TRIM,('bottom',))
        # Only the exposed overhang undersides are drawn; the core top is
        # covered by the nosing, so no duplicate coplanar top remains.
        side=spec['nosing_side_m'];front=spec['nosing_front_m'];low=top-spec['nosing_height_m']
        for xa,xb,ya,yb in ((fx0-side,fx0,a,c),(fx1,fx1+side,a,c),
                           (fx0-side,fx1+side,a-front,a)):
            b.raw([(xa,ya,low),(xb,ya,low),(xb,yb,low),(xa,yb,low)],conf,d.TRIM,(0,0,-1))
    # The visible cheek is stepped beneath the tread stones. Its inner face
    # is buried in the stair core, not another exposed masonry surface.
    outer=fx1+spec['cheek_outer_m'];base=spec['cheek_base_m']
    top=z-spec['nosing_height_m']
    face=[(outer,fy0,base),(outer,fy1,base),(outer,fy1,top),(outer,fy0,top)]
    holes=[]
    for i in range(count-1):
        a=fy0+i*run;c=a+run;h=rise*(i+1)-spec['nosing_height_m']
        holes.append([(outer,a,h),(outer,c,h),(outer,c,top+.1),(outer,a,top+.1)])
    if getattr(b,'reduced_service_access',False):
        for i in range(count):
            a=fy0+i*run;c=a+run;h=rise*(i+1)-spec['nosing_height_m']
            b.raw([(outer,a,base),(outer,c,base),(outer,c,h),(outer,a,h)],conf,flat_brick(b),(1,0,0))
    else:b.wall(face,conf,d.BRICK,custom_holes=holes)
    for i in range(1,count):
        y=fy0+i*run;low=rise*i;high=rise*(i+1)-spec['nosing_height_m']
        b.raw([(fx1,y,low),(outer,y,low),(outer,y,high),(fx1,y,high)],conf,flat_brick(b),(0,-1,0))
    for y,h,want in ((fy0,rise-spec['nosing_height_m'],(0,-1,0)),(fy1,top,(0,1,0))):
        b.raw([(fx1,y,base),(outer,y,base),(outer,y,h),(fx1,y,h)],conf,flat_brick(b),want)

    inset=rail['edge_inset_m'];xl=fx0+inset;xr=fx1-inset
    bottom_y=fy0+rail['first_post_inset_m'];knee_y=fy1-run
    front_y=y0+inset;back_y=y1-inset;far_x=x1-inset;left_x=x0+inset
    def guide(y):return min(z,rise+(y-fy0)*rise/run)
    paths=[[(xl,bottom_y,guide(bottom_y)),(xl,knee_y,z),(xl,front_y,z),
            (left_x,front_y,z),(left_x,back_y,z)],
           [(xr,bottom_y,guide(bottom_y)),(xr,knee_y,z),(xr,front_y,z),
            (far_x,front_y,z),(far_x,back_y,z)]]
    for line in paths:
        for fraction in [*rail['lower_fractions'],1.0]:
            points=[(x,y,base+fraction*s['rail_height_m']) for x,y,base in line]
            _rail(b,points,rail['top_width_m'] if fraction==1 else rail['lower_width_m'],
                  rail['top_thickness_m'] if fraction==1 else rail['lower_thickness_m'],conf)
    # Posts seat on actual treads, independently of the continuous rail pitch.
    positions=[]
    for x in (xl,xr):
        for i in rail['flight_post_treads']:
            y=bottom_y if i==0 else fy0+(i+.5)*run
            positions.append((x,y,rise*(i+1),guide(y)))
        if x==xr:positions.append((x,front_y,z,z))
    positions.extend([(left_x,front_y,z,z),(left_x,back_y,z,z),((xr+far_x)/2,front_y,z,z),
                      (far_x,front_y,z,z),(far_x,back_y,z,z)])
    b.service_posts=[];seen=set()
    for x,y,base,top_base in positions:
        key=(round(x,7),round(y,7))
        if key in seen:continue
        seen.add(key);h=rail['foot_width_m']/2;plate=base+rail['foot_thickness_m']
        _box(b,(x-h,y-h,base),(x+h,y+h,plate),conf,d.IRON,('bottom',))
        top=top_base+s['rail_height_m']
        d.cylinder(b,x,y,plate,top,rail['post_radius_m'],conf,d.IRON,6)
        b.service_posts.append({'x':x,'y':y,'seat':base,'plate_top':plate,'top':top,'foot_width':2*h})


def _board_leaf(b,at,lo,hi,bottom,top,spec,conf):
    from archetypes import masonry_house_v4_detail as d
    half=spec['leaf_thickness_m']/2;depth=spec['groove_depth_m']
    _box(b,(at-half+depth,lo,bottom),(at+half-depth,hi,top),conf,d.WOOD)
    count=max(1,round((hi-lo)/spec['board_width_m']));pitch=(hi-lo)/count
    for i in range(count):
        a=lo+i*pitch+(spec['board_joint_m']/2 if i else 0)
        q=lo+(i+1)*pitch-(spec['board_joint_m']/2 if i<count-1 else 0)
        for side in (-1,1):
            outer=at+side*half;inner=at+side*(half-depth)
            _box(b,(min(inner,outer),a,bottom),(max(inner,outer),q,top),conf,d.WOOD,
                 ('right',) if side<0 else ('left',))


def build_jamb_piece(b,w):
    """Dress only the two gate reveals; exterior stone keeps its rock faces."""
    from archetypes import masonry_house_v4_detail as d
    if 'ends' in w or w.get('kind') not in ('wall','pier') or w.get('axis')!='x':return False
    gate=next((g for g in b.params.walls if g.get('kind')=='gate' and g.get('axis')=='x' and abs(g['at']-w['at'])<1e-7),None)
    if gate is None:return False
    if abs(w['u1']-gate['u0'])<1e-7:face='back';u=w['u1'];want=(0,1,0)
    elif abs(w['u0']-gate['u1'])<1e-7:face='front';u=w['u0'];want=(0,-1,0)
    else:return False
    conf=b.params.conf('service_access_details');x0=w['at']-w['thick_m']/2;x1=w['at']+w['thick_m']/2
    old=b.decorate
    try:
        b.decorate=True
        b.add_box(x0,w['u0'],0,x1,w['u1'],w['z1'],w['conf'],d.GRANITE,skip=('bottom',face))
        had='block' in b.__dict__;original=b.block
        def dressed(polygon,point,normal,confidence,mat,rng,holes=None,course=None):
            # Keep the established course schedule and its mortar bed. Dress
            # the reveal flush so rock-face relief cannot bury the hinge pins
            # (so a course's own crown, T-3046, has nothing to raise here).
            variant=12+rng.randrange(4)
            for fragment in d.subtract(polygon,holes or []):
                b.raw([point(q,0) for q in fragment],confidence,variant,normal)
                for a,q in zip(fragment,fragment[1:]+fragment[:1]):
                    b.raw([point(a,-.009),point(q,-.009),point(q,0),point(a,0)],confidence,variant)
                b.masonry_blocks+=1
        try:
            b.block=dressed
            points=[(x0,u,0),(x1,u,0),(x1,u,w['z1']),(x0,u,w['z1'])]
            if d.dot(d.legacy._normal(points),want)<0:points.reverse()
            b.wall(points,conf,d.GRANITE)
        finally:
            if had:b.block=original
            else:del b.block
        over=.06
        _box(b,(x0-over,w['u0']-over,w['z1']),
             (x1+over,w['u1']+over,w['z1']+d.legacy.COPING_H),w['conf'],d.TRIM)
    finally:
        b.decorate=old
    if not hasattr(b,'service_jambs'):b.service_jambs=[]
    b.service_jambs.append({'at':u,'normal':want,'x':[x0,x1],'top':w['z1'],'dressed':True})
    return True


def _brace(b,at,back,low_y,high_y,low_z,high_z,width,conf):
    """Compression brace butts into the ledges, without overlapping face planes."""
    from archetypes import masonry_house_v4_detail as d
    first=len(b.faces)
    dy=high_y-low_y;dz=high_z-low_z
    half=width*math.hypot(dy,dz)/(2*abs(dz))
    shape=[(low_y-half,low_z),(low_y+half,low_z),(high_y+half,high_z),(high_y-half,high_z)]
    for x,want in ((at,(-1,0,0)),(back,(1,0,0))):
        b.raw([(x,y,z) for y,z in shape],conf,d.WOOD,want)
    for i in (1,3):
        a=shape[i];q=shape[(i+1)%4]
        want=(0,(a[0]+q[0]-low_y-high_y)/2,(a[1]+q[1]-low_z-high_z)/2)
        b.raw([(at,*a),(back,*a),(back,*q),(at,*q)],conf,d.WOOD,want)
    grain_members(b,first,(0,dy,dz),(at,low_y,low_z))


def build_gate(b,w):
    from archetypes import masonry_house_v4_detail as d
    if w['axis']!='x':raise ValueError('The service-access gate detail requires the retained west opening')
    spec=b.params.detail['service_access']['gate'];conf=b.params.conf('service_access_details')
    at=w['at'];u0=w['u0'];u1=w['u1'];mid=(u0+u1)/2
    bottom=spec['threshold_top_m']+spec['bottom_clearance_m'];top=w['z1']
    threshold=spec['threshold_width_m']/2
    _box(b,(at-threshold,u0,spec['threshold_bottom_m']),(at+threshold,u1,spec['threshold_top_m']),conf,d.GRANITE,('bottom',))
    leaves=[(u0+spec['jamb_gap_m'],mid-spec['centre_gap_m']/2,1),
            (mid+spec['centre_gap_m']/2,u1-spec['jamb_gap_m'],-1)]
    b.service_gate={'leaves':[],'hinges':[],'threshold_top':spec['threshold_top_m'],'threshold_bottom':spec['threshold_bottom_m']}
    for lo,hi,direction in leaves:
        _board_leaf(b,at,lo,hi,bottom,top,spec,conf)
        back=at+spec['leaf_thickness_m']/2
        levels=[bottom+(top-bottom)*fraction for fraction in spec['hinge_fractions']]
        for z in levels:
            first=len(b.faces)
            _box(b,(back,lo,z-spec['ledge_height_m']/2),
                 (back+spec['ledge_depth_m'],hi,z+spec['ledge_height_m']/2),conf,d.WOOD,('left',))
            grain_members(b,first,(0,1,0),(back,lo,z))
        near=lo if direction>0 else hi;far=hi if direction>0 else lo
        margin=spec['brace_width_m']
        _brace(b,back,back+spec['ledge_depth_m'],near+direction*margin,far-direction*margin,
               levels[0]+spec['ledge_height_m']/2,levels[1]-spec['ledge_height_m']/2,spec['brace_width_m'],conf)
        jamb=u0 if direction>0 else u1
        axis_y=jamb+direction*spec['pin_jamb_inset_m'];axis_x=back+spec['pin_leaf_offset_m']
        for z in levels:
            # The reveal plate touches masonry, and both strap and plate enter
            # the pin's radius. No hinge floats between leaf and jamb.
            ya,yb=sorted((jamb-direction*.015,jamb+direction*.006))
            _box(b,(at,ya,z-spec['pin_height_m']/2),(at+.12,yb,z+spec['pin_height_m']/2),conf,d.IRON)
            sa,sb=sorted((near,near+direction*spec['strap_length_m']))
            sx=back+spec['ledge_depth_m']
            _box(b,(sx,sa,z-spec['strap_height_m']/2),(sx+spec['strap_thickness_m'],sb,z+spec['strap_height_m']/2),conf,d.IRON,('left',))
            # The pin is tangent to the ledge's outside face. The strap meets
            # it directly; burying its axis behind that face hides the hinge.
            d.cylinder(b,axis_x,axis_y,z-spec['pin_height_m']/2,z+spec['pin_height_m']/2,
                       spec['pin_radius_m'],conf,d.IRON,8)
            for pz,want in ((z-spec['pin_height_m']/2,(0,0,-1)),(z+spec['pin_height_m']/2,(0,0,1))):
                b.raw([(axis_x+spec['pin_radius_m']*math.cos(2*math.pi*i/8),
                        axis_y+spec['pin_radius_m']*math.sin(2*math.pi*i/8),pz) for i in range(8)],conf,d.IRON,want)
            b.service_gate['hinges'].append({'axis':[axis_x,axis_y,z],'jamb':jamb,'radius':spec['pin_radius_m'],'strap_x':sx})
        b.service_gate['leaves'].append({'lo':lo,'hi':hi,'bottom':bottom,'top':top})
    # Plain latch across the meeting stiles; its keeper seats on the other leaf.
    x=at+spec['leaf_thickness_m']/2;z=spec['latch_height_m'];t=spec['strap_thickness_m']
    _box(b,(x,mid-.13,z-.025),(x+t,mid+.12,z+.025),conf,d.IRON,('left',))
    # An open keeper bridges over the bar; a solid block would bury the latch.
    for low,high in ((z-.04,z-.03),(z+.03,z+.04)):
        _box(b,(x,mid+.065,low),(x+3*t,mid+.095,high),conf,d.IRON,('left',))
    _box(b,(x+2*t,mid+.065,z-.03),(x+3*t,mid+.095,z+.03),conf,d.IRON,('top','bottom'))
    b.service_gate['latch']={'keeper_y':mid+.08,'height':z}

