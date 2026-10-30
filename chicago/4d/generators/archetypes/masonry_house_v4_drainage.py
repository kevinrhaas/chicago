"""T-2221: photographed head families and a connected rainwater network.

All dimensions are bounded reconstructions in rainwater_details, not measured
1904 fittings. Taylor supplies the Prairie panels; HABS01/14 the north heads;
licensed modern court photographs bound box stock, not its 1904 colour or age.
Legacy versions retain their original rainwater builder. Coordinates are local
east/north/up metres. Gutters inherit roof edges; roofs never inherit gutters.
"""
from __future__ import annotations

import math
from archetypes.masonry_house_v4_rainwater import _unit, _cross

METAL = 28  # dedicated oxidised rainwater finish; existing iron hardware stays dark
CONF = 1.0  # reconstructed; do not promote stock dimensions to attested


def layout(p,reduced=False):
    """Return named roof collectors, downpipes and descending branch connections."""
    cfg = p.detail['rainwater']
    rs = {r['name']: r for r in p.ranges}
    e, n, w = (rs[k] for k in ('east_wing', 'north_range', 'west_wing'))
    bow = next(t for t in p.bows if t['name'] == 'hall_bow')
    dining = next(t for t in p.bays if t['name'] == 'dining')
    tower = next(t for t in p.towers if t['name'] == 'north')
    stair = next(t for t in p.towers if t['name'] == 'stair')
    from archetypes.masonry_house_v4_west_roof import height, profile
    from archetypes.masonry_house_v4_courtyard_roof import north_height
    gutters, leaders, branches = [], [], []
    depth = cfg['gutter_depth_m']

    def gutter(name, edge, normals, drains):
        gutters.append(dict(name=name, edge=edge, normals=normals, drains=drains))

    def leader(name, inlet, xy, normal, wall, head='plain', shoe=False, drop=0.0):
        family=cfg.get('leader_profiles',{}).get('prairie' if name.startswith('prairie-') else
                   'court_feature' if name in ('court-dining','court-bow') else 'plain',{})
        head_h = cfg['heads'][head]['height_m'] if head != 'none' else 0
        # Photographed heads rise to the gutter rim; the trough discharges
        # inside their upper body. Do not hang the entire head below the floor.
        # `drop` hangs a drawn head that far under the rim instead (T-2926).
        mouth = inlet[2] + .025 - drop if head!='none' else inlet[2]-depth-.035
        top = mouth - head_h + .025
        upper = (inlet[0], inlet[1], top)
        shoulder = min(top-.18, mouth-head_h-.12)
        mount=(xy[0],xy[1],shoulder)
        path = [upper,(*upper[:2],upper[2]-.09),mount,(xy[0],xy[1],.10 if shoe else -.06)]
        if shoe:
            path += [(xy[0]+normal[0]*.17, xy[1]+normal[1]*.17, .065)]
        outlet_end=inlet[2]-depth-.05 if head!='none' else path[0][2]-.03
        spout=[(*inlet[:2],inlet[2]-.07),(*inlet[:2],outlet_end)]
        leaders.append(dict(name=name, inlet=inlet, path=path, normal=normal,
                            wall=wall, head=head, mouth=mouth, shoe=shoe,spout=spout,mount=mount,**family))
        return leaders[-1]

    # Prairie Avenue: early Taylor photograph shows two rectangular panels,
    # narrow necks and three broad straps. No modern inspection caps.
    ex = e['x1']+.20
    ez = e['eave_hi_z']-.20*(e['ridge_z']-e['eave_hi_z'])/(e['x1']-e['ridge_at'])
    for name, y in (('prairie-south', e['y0']+.18), ('prairie-north', e['y1']-.18)):
        leader(name, (ex+.045, y, ez), (e['x1']+.13, y), (1,0,0), e['x1'], 'panel')
    gutter('prairie', [(ex,e['y0'],ez),(ex,e['y1'],ez)], [(1,0,0)]*2,
           ['prairie-south','prairie-north'])

    # 18th Street: the north tower's upper leader actually enters a bowl.
    # Its mouth sits against the retained lower roof, not at an invented eave.
    angle = math.radians(cfg['north_pipe_angle_deg'])
    u = (math.cos(angle),math.sin(angle),0)
    tx = tower['cx']+(tower['r']+.08)*u[0]
    ny = n['y1']+.20
    nz = north_height(p,ny)
    foot = p.detail['north_service_junction']['gable_foot_x']
    leader('north-service', (foot,ny+.045,nz), (foot,n['y1']+.13), (0,1,0), n['y1'])
    head = leader('north-tower', (tx,ny+.045,nz), (tx,n['y1']+.13), (0,1,0), n['y1'], 'bowl')
    gutter('north-street', [(foot,ny,nz),(tx,ny,nz)], [(0,1,0)]*2,
           ['north-service','north-tower'])
    upper = (tower['cx']+(tower['eave_r']+.045)*u[0],tower['cy']+(tower['eave_r']+.045)*u[1],
             tower['wall_top_z']-depth-.012)
    wall_xy = (tower['cx']+(tower['r']+.08)*u[0],tower['cy']+(tower['r']+.08)*u[1])
    branches.append(dict(name='tower-upper', target='north-tower', width=cfg['upper_pipe_width_m'],
                         normal=u, path=[upper,(*upper[:2],upper[2]-.10),(*wall_xy,upper[2]-.38),
                         (*wall_xy,nz+.36),(tx,ny+.045,head['mouth']-.09)]))
    count=16 if reduced else 24
    angles=[math.pi/2+math.pi*i/count for i in range(count+1)]
    gutter('north-tower-upper',
           [(tower['cx']+tower['eave_r']*math.cos(a),tower['cy']+tower['eave_r']*math.sin(a),tower['wall_top_z']) for a in angles],
           [(math.cos(a),math.sin(a),0) for a in angles],[])
    gutters[-1]['branch']='tower-upper'
    branches[-1]['support']={'path':[upper,(*wall_xy,upper[2]-.40)],'base':nz+.45,
                            'normal':u,'width':cfg['upper_pipe_width_m'],
                            'wall':{'centre':(tower['cx'],tower['cy']),'r':tower['r']}}

    # Small north-facing eave beside the stable gable; never cross its rake.
    wz = height(w,w['x0'],w['y1'])
    gx = w['x0']+.12
    leader('alley-north', (gx,ny+.045,wz), (gx,w['y1']+.13), (0,1,0), w['y1'])
    gutter('stable-north', [(w['x0']-.15,ny,wz),(w['stable_roof']['front_x0'],ny,wz)],
           [(0,1,0)]*2, ['alley-north'])
    join = profile(w,'west')[-3][0]
    x = w['x0']-.17
    z = height(w,w['x0'],w['y0'])-.025
    for name,y in (('alley-rear',w['y0']+.08),('alley-middle',join-.08)):
        leader(name,(x-.045,y,z),(w['x0']-.13,y),(-1,0,0),w['x0'],shoe=True)
    gutter('alley-low',[(x,w['y0'],z),(x,join,z)],[(-1,0,0)]*2,['alley-rear','alley-middle'])

    # Court box troughs: the curved bow retains its curved plan. Each isolated
    # eave fragment has its own path to grade, clear of photographed openings.
    over = n['eave_lo_overhang']
    cy = n['y0']-over
    cz = n['eave_lo_z']-over*(n['ridge_z']-n['eave_lo_z'])/(n['ridge_at']-n['y0'])
    wx = w['stable_roof']['court_edge_x']
    wz = w['stable_roof']['court_edge_z']
    leader('court-west',(wx+.045,w['y0']+.10,wz),(w['x1']+.13,w['y0']+.10),
           (1,0,0),w['x1'],'none',True)
    corner=(1,-1,0)
    gutter('court-west',[(wx,w['y0'],wz),(wx,cy,wz)],[(1,0,0),corner],['court-west'])
    outline = dining['pts'][1:-1]
    # Miter bisectors preserve the width at angular bay corners.
    normals=[]
    for i,q in enumerate(outline):
        a,c=outline[max(0,i-1)],outline[min(len(outline)-1,i+1)]
        before=_unit((q[1]-a[1],a[0]-q[0],0)) if i else (0,-1,0)
        after=_unit((c[1]-q[1],q[0]-c[0],0)) if i<len(outline)-1 else (0,-1,0)
        denom=1+sum(before[k]*after[k] for k in range(3))
        normals.append(tuple((before[k]+after[k])/denom for k in range(3)))
    d0,d1=outline[0],outline[-1]
    leader('court-dining',(d0[0]-.045,d0[1]-.045,cz),(d0[0]-.10,n['y0']-.13),
           (0,-1,0),n['y0'],'none',True)
    gutter('dining', [(*q,cz) for q in outline],normals,['court-dining'])
    gutter('court-north-west',[(wx,cy,cz),(d0[0],cy,cz)],[corner,normals[0]],['court-dining'])
    a0,a1=sorted((bow['a0'],bow['a1']))
    if a1-a0>math.pi:a0,a1=a1,a0+2*math.pi
    radius=bow['eave_r']
    count=24 if reduced else 48
    angles=[a0+(a1-a0)*i/count for i in range(count+1)]
    edge=[(bow['cx']+radius*math.cos(a),bow['cy']+radius*math.sin(a),bow['wall_top_z']) for a in angles]
    bx=bow['cx']+bow['r']*math.cos(a0)-.085
    by=n['y0']-.085
    bn=_unit((bx-bow['cx'],by-bow['cy'],0))
    # Radial wall coordinate used by collars; the circular masonry surface is
    # intersected explicitly instead of attaching to an imaginary flat plane.
    section,mid={},.045
    if 'bow_gutter' in cfg:
        # T-2861: sheet 4's trough, its face set out from the bow's wall, not the hood;
        # its outlet at the narrower trough's middle.
        g=cfg['bow_gutter']
        section=dict(width_m=g['projection_m']-(radius-bow['r'])+.035,depth_m=g['depth_m'])
        mid=section['width_m']/2-.035
    leader('court-bow',(edge[0][0]+mid*math.cos(a0),edge[0][1]+mid*math.sin(a0),bow['wall_top_z']),
           (bx,by),bn,{'centre':(bow['cx'],bow['cy']),'r':bow['r']},'none',True)
    gutter('bow',edge,[(math.cos(a),math.sin(a),0) for a in angles],['court-bow'])
    if section:gutters[-1]['section']=section
    if 'bow_leader' in cfg:
        # T-2939: sheet 4 draws this leader side-on, standing on the north range's court face
        # in its corner with the bow: a head hung under the trough's floor with its back on the
        # line of that wall, its front stepping in to the pipe's 100 mm side; so the pipe's broad face
        # looks south. The drop from the trough's outlet into the head is inside the head.
        g=cfg['bow_leader'];row=leaders[-1]
        pd=row['depth_m']
        floor=row['inlet'][2]-section.get('depth_m',depth)-.012
        front=n['y0']-g['head_depth_m']
        bx=bow['cx']-math.sqrt(bow['r']**2-(front-bow['cy'])**2)-g['head_width_m']/2-.005
        by=n['y0']-pd/2-.003
        ix=row['inlet'][0]  # the drop keeps to the pipe's line, south of the wall face
        row.update(normal=(0,-1,0),wall=n['y0'],mouth=floor,mount=(bx,by,floor-g['head_straight_m']),
                   spout=[(ix,by,row['spout'][0][2]),(ix,by,floor-.005)],
                   path=[(ix,by,floor-.005),(bx,by,floor-.06),(bx,by,floor-g['head_straight_m']),
                         (bx,by,.10),(bx,by-.17,.065)],
                   hopper=dict(centre=(bx,n['y0']-.003,floor),width=g['head_width_m'],depth=g['head_depth_m'],
                               straight=g['head_straight_m'],height=g['head_height_m'],neck=pd,
                               studs=g.get('studs',[])))
        bn=row['normal']
    right=bow['cx']-math.sqrt(radius*radius-(cy-bow['cy'])**2)
    gutter('court-north-east',[(d1[0],cy,cz),(right,cy,cz)],[normals[-1],(0,-1,0)],[])
    branches.append(dict(name='court-north-bow', target='court-bow', width=cfg['pipe_width_m'],
        normal=bn, path=[(right-.05,cy-.045,cz-depth),(right-.05,cy-.045,cz-.22),
                        (bx,by,cz-.40)]))
    gutters[-1]['branch']='court-north-bow'
    ex=e['x0']-.20
    ez=e['eave_lo_z']-.20*(e['ridge_z']-e['eave_lo_z'])/(e['ridge_at']-e['x0'])
    end=bow['cy']-math.sqrt(radius*radius-(ex-bow['cx'])**2)
    half=math.sqrt(stair['r']**2-(ex-stair['cx'])**2)+.025
    for name,a,c,y in (('court-east-south',e['y0'],stair['cy']-half,stair['cy']-half-.16),
                        ('court-east-north',stair['cy']+half,end,stair['cy']+half+.16)):
        # The surveyed tower position and broad garden light leave different
        # clear wall strips than the earlier tangent-based reconstruction.
        # Explicit record anchors keep both leaders and their straps off glass.
        if name in cfg.get('court_east_into_bow',()):
            # T-2928: sheet 4 draws no leader on the strip between the bow and the
            # stair tower; its gutter runs on to the end of the bow's trough, whose
            # leader (court-bow) takes the water. The junction is not drawn.
            gutter(name,[(ex,a,ez),(ex,c,ez)],[(-1,0,0)]*2,[])
            gutters[-1]['feeds']='bow'
            continue
        y=cfg.get('court_east_leaders_y',{}).get(name,y)
        # T-2926: sheet 4 draws the south one under a hopper head.
        head=cfg.get('court_east_leader_heads',{}).get(name,'none')
        leader(name,(ex-.045,y,ez),(e['x0']-.13,y),(-1,0,0),e['x0'],head,True,
               cfg.get('court_east_leader_head_drop_m',{}).get(name,0.0))
        gutter(name,[(ex,a,ez),(ex,c,ez)],[(-1,0,0)]*2,[name])
    open_ends={'court-west':[1],'dining':[0,1],'court-north-west':[0,1],'court-north-east':[0]}
    for row in gutters:row['open_ends']=open_ends.get(row['name'],[])
    return dict(gutters=gutters,leaders=leaders,branches=branches)


def _raw(b, pts, want):
    b.raw(pts,CONF,METAL,want)


def _sweep(b,path,profile,normal,caps=False):
    """Open-ended folded stock along a path, sharing corner rings at bends."""
    rings=[]
    for i,p in enumerate(path):
        a,c=path[max(0,i-1)],path[min(len(path)-1,i+1)]
        t=_unit(tuple(c[k]-a[k] for k in range(3)))
        u=_unit(_cross(t,normal));v=_cross(u,t)
        rings.append([tuple(p[k]+q[0]*u[k]+q[1]*v[k] for k in range(3)) for q in profile])
    for i in range(len(path)-1):
        for j in range(len(profile)):
            q=(j+1)%len(profile)
            pts=[rings[i][j],rings[i][q],rings[i+1][q],rings[i+1][j]]
            centre=tuple((path[i][k]+path[i+1][k])/2 for k in range(3))
            _raw(b,pts,tuple(sum(p[k] for p in pts)/4-centre[k] for k in range(3)))
    if caps:
        for i,other in ((0,1),(-1,-2)):
            _raw(b,rings[i],tuple(path[i][k]-path[other][k] for k in range(3)))


def _pipe(b,path,width,normal,depth=None,flutes=0,relief=0):
    h=width/2;d=(depth or width)/2
    profile=[(-h,-d),(h,-d),(h,d)]
    if flutes:
        profile += [(h-width*j/(2*flutes),d+(relief if j%2 else 0)) for j in range(1,2*flutes+1)]
    else:profile.append((-h,d))
    _sweep(b,path,profile,normal)


def _rod(b,path,radius,normal,sides):
    _sweep(b,path,[(radius*math.cos(2*math.pi*i/sides),radius*math.sin(2*math.pi*i/sides))
                  for i in range(sides)],normal,True)


def _band(b,centre,width,depth,height,normal,stock=.006):
    """Raised collar whose top and bottom return into the underlying body."""
    x,y,z=centre;nx,ny,_=normal;tx,ty=-ny,nx
    def ring(w,d,h):
        return [(x+tx*a+nx*c,y+ty*a+ny*c,z+h)
                for a,c in [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)]]
    lo,hi=ring(width,depth,-height/2),ring(width,depth,height/2)
    for j in range(4):
        k=(j+1)%4;pts=[lo[j],lo[k],hi[k],hi[j]]
        _raw(b,pts,(sum(q[0] for q in pts)/4-x,sum(q[1] for q in pts)/4-y,0))
    for outer,h,sign in ((lo,-height/2,-1),(hi,height/2,1)):
        inner=ring(width-2*stock,depth-2*stock,h)
        for j in range(4):
            k=(j+1)%4;_raw(b,[outer[j],outer[k],inner[k],inner[j]],(0,0,sign))


def _head(b,centre,normal,spec,kind,reduced):
    """Open sheet-metal receiver, moulded rim/neck and family-specific relief."""
    x,y,z=centre;nx,ny,_=normal;tx,ty=-ny,nx
    w,d,h=spec['width_m'],spec['depth_m'],spec['height_m']
    neck=spec['neck_m'];stock=.003
    profile = ([(0,w,d),(-.08*h,w,d),(-.18*h,w*.83,d*.90),
                (-.70*h,neck*1.35,neck*1.35),(-.79*h,neck,neck),(-h,neck,neck)]
               if kind=='bowl' else
               [(0,w,d),(-.10*h,w,d),(-.16*h,w*.82,d*.85),
                (-.77*h,w*.76,d*.78),(-.91*h,neck,neck),(-h,neck,neck)]
               if kind=='panel' else [(0,w,d),(-.12*h,w,d),(-h,neck,neck)])
    def ring(q,inset):
        dz,ww,dd=q;ww=ww/2-inset;dd=dd/2-inset
        return [(x+tx*a+nx*c,y+ty*a+ny*c,z+dz) for a,c in [(-ww,-dd),(ww,-dd),(ww,dd),(-ww,dd)]]
    for inset,inward in ((0,False),(stock,True)):
        for a,c in zip(profile,profile[1:]):
            ra,rc=ring(a,inset),ring(c,inset)
            for j in range(4):
                k=(j+1)%4;pts=[ra[j],ra[k],rc[k],rc[j]]
                want=(sum(v[0] for v in pts)/4-x,sum(v[1] for v in pts)/4-y,0)
                _raw(b,pts,tuple(-v for v in want) if inward else want)
    for q,sign in ((profile[0],1),(profile[-1],-1)):
        outer,inner=ring(q,0),ring(q,stock)
        for j in range(4):
            k=(j+1)%4;_raw(b,[outer[j],outer[k],inner[k],inner[j]],(0,0,sign))
    # Two socket beads, with open bores. No solid lid hides the inlet.
    for dz in (-.04*h,-.94*h):
        ww,dd=(w,d) if dz>-.5*h else (neck,neck)
        _band(b,(x,y,z+dz),ww+.016,dd+.016,.024,normal,.010)
    if kind=='bowl':
        # Raised ribs converge along the flared face in HABS14. Ornament is
        # bounded low relief, not a traced claim about an unreadable casting.
        for f in (-.72,-.24,.24,.72):
            a=(x+tx*w*.40*f+nx*d*.455,y+ty*w*.40*f+ny*d*.455,z-.19*h)
            c=(x+tx*neck*.65*f+nx*neck*.69,y+ty*neck*.65*f+ny*neck*.69,z-.69*h)
            _rod(b,[a,c],.007,normal,4 if reduced else 6)
    elif kind=='panel':
        def point(a,zz,front):return (x+tx*a+nx*front,y+ty*a+ny*front,z+zz)
        face=d*.425+spec.get('frame_relief_m',.014)
        frame=[point(-w*.31,-h*.23,face),point(w*.31,-h*.23,face),
               point(w*.285,-h*.70,face*.94),point(-w*.285,-h*.70,face*.94)]
        for a,c in zip(frame,frame[1:]+frame[:1]):
            _rod(b,[a,c],spec.get('frame_stock_m',.024)/2,normal,4 if reduced else 6)
        boss=point(0,-h*.46,face+.009)
        _rod(b,[boss,tuple(boss[k]+normal[k]*.018 for k in range(3))],
             w*spec.get('boss_width_fraction',.38)/2,(0,0,1),8 if reduced else 12)


def _hopper(b,spec,reduced):
    """T-2939: a wall head drawn side-on, its back flat on a south-facing wall and its
    front stepping in to the pipe. Open top; the studs are the drawn round features
    on its west side, each a shallow disc."""
    x,wall,z=spec['centre'];w=spec['width'];stock=.003
    profile=[(0,spec['depth']),(-spec['straight'],spec['depth']),(-spec['height'],spec['neck']+2*stock)]
    def ring(q,inset):
        dz,d=q;ww=w/2-inset
        return [(x+a,wall-c,z+dz) for a,c in [(-ww,inset),(ww,inset),(ww,d-inset),(-ww,d-inset)]]
    centre=lambda q:(x,wall-q[1]/2,z+q[0])
    for inset,inward in ((0,False),(stock,True)):
        for a,c in zip(profile,profile[1:]):
            ra,rc=ring(a,inset),ring(c,inset)
            for j in range(4):
                k=(j+1)%4;pts=[ra[j],ra[k],rc[k],rc[j]]
                o=centre(a);want=tuple(sum(v[i] for v in pts)/4-o[i] for i in range(3))
                want=(want[0],want[1],0)
                _raw(b,pts,tuple(-v for v in want) if inward else want)
    for q,sign in ((profile[0],1),(profile[-1],-1)):
        outer,inner=ring(q,0),ring(q,stock)
        for j in range(4):
            k=(j+1)%4;_raw(b,[outer[j],outer[k],inner[k],inner[j]],(0,0,sign))
    for s in spec['studs']:
        a=(x-w/2+.002,wall-s['off_wall_m'],z-s['below_top_m'])
        _rod(b,[a,(a[0]-s['proud_m'],a[1],a[2])],s['diameter_m']/2,(0,0,1),8 if reduced else 16)


def _attachments(b,row,cfg):
    """Broad wrap straps, wall-return tabs and studs; no freestanding collars."""
    x,y,top=row.get('mount',row['path'][1]);normal=row['normal'];nx,ny,_=normal;tx,ty=-ny,nx
    width=row.get('width_m',row.get('width',cfg['pipe_width_m']));half=width/2
    depth=row.get('depth_m',width)
    span=row.get('strap_span_m',.17)
    band_height=row.get('strap_height_m',.05)
    base=row.get('base',.18)
    heights=row.get('strap_z_m',[base+(top-base)*f for f in row.get('strap_fractions',(.18,.48,.78))])
    for z in heights:
        _band(b,(x,y,z),width+.014,depth+.014,band_height,normal,.008)
        for sign in (-1,1):
            a=(x+tx*sign*span/2,y+ty*sign*span/2,z)
            if isinstance(row['wall'],dict):
                centre=row['wall']['centre'];radius=row['wall']['r']
                dx,dy=a[0]-centre[0],a[1]-centre[1]
                # Offset line/circle intersection along the outward normal.
                dot=dx*nx+dy*ny
                gap=dot-math.sqrt(max(0,dot*dot-(dx*dx+dy*dy-radius*radius)))
            else:
                gap=(a[0]-row['wall'])*nx if nx else (a[1]-row['wall'])*ny
            c=(a[0]-nx*(gap+.025),a[1]-ny*(gap+.025),z)
            # The projecting ear returns directly from wrap to wall. Its
            # stone-side end is buried 25 mm into the masonry relief.
            _pipe(b,[c,(x+tx*sign*half,y+ty*sign*half,z)],.028,(0,0,1),depth=band_height)


def _gutter(b,row,cfg,outlets):
    """Thin box trough with rolled front edge and open floor at each outlet."""
    edge,normals=row['edge'],row['normals'];s=cfg['stock_m']
    depth=row.get('section',{}).get('depth_m',cfg['gutter_depth_m'])
    width=row.get('section',{}).get('width_m',cfg['gutter_width_m'])
    # Two-dimensional section in outward/up coordinates. Both surfaces and
    # rolled lip have stock; no black zero-thickness planes at close range.
    back,front=-.035,width-.035
    section=[(back,0),(back,-depth),(front,-depth),(front,.008),
             (front-.012,.008),(front-.012,.008-s),(front-s,.008-s),
             (front-s,-depth+s),(back+s,-depth+s),(back+s,0)]
    floors=(1,7)
    if getattr(b,'reduced_roof_details',False):
        # Only the 12 mm folded lip is simplified. Light retains the same
        # collector path, stock thickness, open bore and outside silhouette.
        section=[(back,0),(back,-depth),(front,-depth),(front,.008),
                 (front-s,.008),(front-s,-depth+s),(back+s,-depth+s),(back+s,0)]
        floors=(1,5)
    def point(i,q):
        return (edge[i][0]+normals[i][0]*q[0],edge[i][1]+normals[i][1]*q[0],edge[i][2]+q[1]-.012)
    from archetypes.masonry_house_v4_north_tower import _half
    from archetypes.masonry_house_v4_west_roof import area
    def subtract(poly,holes):
        result=[poly]
        for hole in holes:
            kept=[]
            for part in result:
                if any(max(v[k] for v in part)<=min(v[k] for v in hole) or
                       min(v[k] for v in part)>=max(v[k] for v in hole) for k in (0,1)):
                    kept.append(part);continue
                remainder=part
                for a,c in zip(hole,hole[1:]+hole[:1]):
                    distance=lambda q:(c[0]-a[0])*(q[1]-a[1])-(c[1]-a[1])*(q[0]-a[0])
                    outside=_half(remainder,lambda q:-distance(q))
                    if outside and abs(area(outside))>1e-10:kept.append(outside)
                    remainder=_half(remainder,distance)
                    if not remainder:break
            result=kept
        return result
    holes=[]
    for outlet in outlets:
        q,n=outlet['point'],outlet['normal'];t=(-n[1],n[0],0)
        h=outlet.get('width',cfg['pipe_width_m'])/2+.001
        d=outlet.get('depth',outlet.get('width',cfg['pipe_width_m']))/2+.001
        # Counterclockwise aperture aligned to the square outlet's own frame.
        holes.append([(q[0]+n[0]*u+t[0]*v,q[1]+n[1]*u+t[1]*v)
                      for u,v in [(-d,-h),(d,-h),(d,h),(-d,h)]])
    for i in range(len(edge)-1):
        for j in range(len(section)):
            k=(j+1)%len(section)
            pts=[point(i,section[j]),point(i,section[k]),point(i+1,section[k]),point(i+1,section[j])]
            # Cut both surfaces, in world XY, including shared miter corners.
            faces=subtract(pts,holes) if j in floors else [pts]
            du=section[k][0]-section[j][0];dz=section[k][1]-section[j][1]
            normal=_unit((normals[i][0]+normals[i+1][0],normals[i][1]+normals[i+1][1],0))
            for face in faces:_raw(b,face,(normal[0]*dz,normal[1]*dz,-du))
    # Sheet-section end closures; leave the trough mouth open.
    for i,other in ((0,1),(-1,-2)):
        if (0 if i==0 else 1) in row['open_ends']:continue
        want=tuple(edge[i][k]-edge[other][k] for k in range(3))
        _raw(b,[point(i,q) for q in section],want)
    # Support arms return beneath the roof edge. At most two metres between
    # arms; a long trough is never a floating strip with no way to carry it.
    distance=0.
    for i,(a,c) in enumerate(zip(edge,edge[1:])):
        length=math.dist(a,c)
        steps=max(1,math.ceil(length/2)) if len(edge)==2 else 1
        for j in range(steps):
            distance+=length/steps
            if len(edge)>2 and distance<1.8:continue
            distance=0.
            f=(j+.5)/steps;n=_unit(tuple(normals[i][k]*(1-f)+normals[i+1][k]*f for k in range(3)))
            p=tuple(a[k]*(1-f)+c[k]*f for k in range(3))
            z=p[2]-depth-.022
            _pipe(b,[(p[0]-n[0]*.075,p[1]-n[1]*.075,p[2]-.04),
                     (p[0]+n[0]*(front-.012),p[1]+n[1]*(front-.012),z)],.022,(0,0,1))


def build(b,p):
    reduced=getattr(b,'reduced_roof_details',False)
    cfg=p.detail['rainwater'];net=layout(p,reduced)
    pipes={r['name']:r for r in net['leaders']}
    branches={r['name']:r for r in net['branches']}
    for row in net['gutters']:
        outlets=[{'point':pipes[k]['inlet'],'normal':pipes[k]['normal'],
                  'width':pipes[k].get('width_m',cfg['pipe_width_m']),
                  'depth':pipes[k].get('depth_m',cfg['pipe_width_m'])} for k in row['drains']]
        if row.get('branch'):
            branch=branches[row['branch']]
            outlets.append({'point':branch['path'][0],'normal':branch['normal'],'width':branch['width']})
        _gutter(b,row,cfg,outlets)
    for row in net['leaders']:
        width=row.get('width_m',cfg['pipe_width_m']);depth=row.get('depth_m',width)
        flutes=row.get('flutes_light' if reduced else 'flutes_full',0)
        _pipe(b,row['path'],width,row['normal'],depth,flutes,row.get('flute_depth_m',0))
        _attachments(b,row,cfg)
        inlet=row['inlet'];head=row['head']
        # Carry water through the actual bottom slot into the receiver or the
        # offset leader. Its lower end overlaps the neck, not a closed cap.
        _pipe(b,row['spout'],width,row['normal'],depth)
        if row.get('hopper'):_hopper(b,row['hopper'],reduced)
        if head!='none':
            _head(b,(*inlet[:2],row['mouth']),row['normal'],cfg['heads'][head],head,reduced)
            spec=cfg['heads'][head];nx,ny,_=row['normal'];tx,ty=-ny,nx
            for sign in (-1,1):
                x,y=inlet[0]+tx*spec['width_m']*.32*sign,inlet[1]+ty*spec['width_m']*.32*sign
                gap=(x-row['wall'])*nx if nx else (y-row['wall'])*ny
                z=row['mouth']-.12
                _pipe(b,[(x-nx*(gap+.025),y-ny*(gap+.025),z),
                         (x-nx*spec['depth_m']*.30,y-ny*spec['depth_m']*.30,z)],.03,(0,0,1))
    for row in net['branches']:
        _pipe(b,row['path'],row['width'],row['normal'])
        if row.get('support'):_attachments(b,row['support'],cfg)
    if getattr(b,'north_tower_details',None):
        b.north_tower_details[-1].update(pipe=branches['tower-upper']['path'],
                                         discharge='north-tower-bowl')
    b.rainwater_network=net
