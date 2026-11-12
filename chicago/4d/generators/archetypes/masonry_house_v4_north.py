"""North stable joinery and masonry reconstructed from the supplied NW view.

HABS owns the apertures; the data record owns the bounded fabric dimensions.
The photo's date is not established, so this 1904 treatment is reconstructed.
No photograph is sampled into a texture and no measured doorway is widened.
"""
from __future__ import annotations

import math
import random


def viewer_right(o):
    """+1 when `u` runs to the right of someone facing the wall, else -1."""
    return 1 if (o['axis']=='x')==(o['sign']>0) else -1


def diagonal_boards(b, o, u0, u1, z0, z1, front, spec, reduced=False, rise=None):
    """T-3564: a panel of boards laid on the diagonal, rising to the viewer's right
    as in the owner's photographs 10-12, each board a face of its own and the
    V-joint between them a dark line set back behind it."""
    from archetypes import masonry_house_v4_detail as v
    if u1-u0<.02 or z1-z0<.02:
        return
    pitch,groove=spec['board_pitch_m'],spec['groove_m']
    n=v.legacy._plane_dir(o)
    if reduced:
        v.slab(b,o,u0,u1,z0,z1,front-.02,front,1.0,v.PAINTED_WOOD)
        return
    v.slab(b,o,u0,u1,z0,z1,front-.03,front-.012,1.0,v.DARK_GLASS)
    k=viewer_right(o) if rise is None else rise
    # A board between the lines z = k*u + c and z = k*u + c + width (vertical width).
    span=(u1-u0)+(z1-z0)
    width=(pitch-groove)*math.sqrt(2)
    c=(z0-k*u0 if k>0 else z0-k*u1)-span
    stop=c+2*span+pitch*math.sqrt(2)
    while c<stop:
        far=(u1-u0)+1
        strip=[(u0-far,k*(u0-far)+c),(u1+far,k*(u1+far)+c),(u1+far,k*(u1+far)+c+width),(u0-far,k*(u0-far)+c+width)]
        piece=v.rect_clip(strip,u0,z0,u1,z1)
        if piece and v.area(piece)>1e-5:
            pts=[v.legacy._plane_point(o,u,z,front) for u,z in piece]
            b.raw(pts,1.0,v.PAINTED_WOOD,n)
        c+=pitch*math.sqrt(2)


def boarded_leaves(b, o, d):
    """T-3564: the coach-house doors as the owner photographed them and ruled them
    "a reasonable representation of the 1904 door": two painted leaves under a
    casing, every panel boarded on the diagonal, and in the leaf on the viewer's
    left a man door, "that people can go in and out of", with a narrow fixed
    panel beside it. The modern kick plates, vision light, signs and the ramp's
    rail and post are left out. Leaf and man-door widths are read off photographs
    10 and 11 against the 12-ft doorway (+/- 0.05 m); reconstructed."""
    from archetypes import masonry_house_v4_detail as v
    a,c,z0,z1=o['u0'],o['u1'],o['z0'],o['z1']
    reduced=getattr(b,'reduced_sash',False)
    W=v.PAINTED_WOOD;conf=1.0
    cas=d['casing_m'];st=d['stile_m'];top=d['top_rail_m'];bot=d['bottom_rail_m'];mid=d['centre_stile_m']
    # The casing round the doorway, proud of the leaves.
    for l,r,lo,hi in [(a,a+cas,z0,z1),(c-cas,c,z0,z1),(a,c,z1-cas,z1)]:
        v.slab(b,o,l,r,lo,hi,-.30,-.205,conf,W)
    la,lc=a+cas,c-cas;lo,hi=z0+.012,z1-cas
    centre=(la+lc)/2
    leaves=((la,centre),(centre,lc))
    panel_front=-.258
    k=viewer_right(o)
    for i,(l,r) in enumerate(leaves):
        inner_l=l+(st if i==0 else mid/2);inner_r=r-(mid/2 if i==0 else st)
        # Stiles and rails of the leaf.
        for sl,sr,sb,stp in [(l,inner_l,lo,hi),(inner_r,r,lo,hi),(inner_l,inner_r,hi-top,hi),(inner_l,inner_r,lo,lo+bot)]:
            v.slab(b,o,sl,sr,sb,stp,-.30,-.245,conf,W)
        # The meeting joint between the leaves.
        if i==0:
            v.slab(b,o,r-.004,r+.004,lo,hi,-.30,-.25,conf,v.DARK_GLASS)
        man=d.get('man_door')
        # The man door hangs in the leaf on the viewer's left: the high-u leaf when
        # u runs to the viewer's left, the low-u one otherwise.
        has_man=man and ((i==1)==(k<0))
        if not has_man:
            diagonal_boards(b,o,inner_l,inner_r,lo+bot,hi-top,panel_front,d,reduced)
            continue
        head=z0+man['head_m'];share=man['width_share'];fr=man['frame_m']
        span=r-l
        # Outer edge of the leaf (hinge side of the pair) is the jamb side.
        if k<0:   # leaf runs from centre (l) to jamb (r); man door against the jamb
            m_out,m_in=r,r-span*share
            fix_l,fix_r=inner_l,m_in
        else:
            m_out,m_in=l,l+span*share
            fix_l,fix_r=m_in,inner_r
        ml,mr=min(m_out,m_in),max(m_out,m_in)
        # Upper panel of the leaf, over the man door's head.
        v.slab(b,o,inner_l,inner_r,head,head+.06,-.30,-.245,conf,W)
        diagonal_boards(b,o,inner_l,inner_r,head+.06,hi-top,panel_front,d,reduced)
        # The fixed narrow panel beside the man door.
        diagonal_boards(b,o,fix_l,fix_r,lo+bot,head,panel_front,d,reduced)
        # The man door: its own frame and boarded panel, outlined by a dark gap.
        for sl,sr,sb,stp in [(ml,ml+fr,lo,head),(mr-fr,mr,lo,head),(ml,mr,head-fr,head),(ml,mr,lo,lo+bot*.8)]:
            v.slab(b,o,sl,sr,sb,stp,-.30,-.245,conf,W)
        diagonal_boards(b,o,ml+fr,mr-fr,lo+bot*.8,head-fr,panel_front,d,reduced)
        for sl,sr,sb,stp in [(ml-.004,ml+.004,lo,head),(mr-.004,mr+.004,lo,head),(ml,mr,head-.004,head+.004)]:
            v.slab(b,o,sl,sr,sb,stp,-.30,-.25,conf,v.DARK_GLASS)
        # Its latch, on the free edge.
        free=m_in+(.09 if m_in>m_out else -.09)
        v.slab(b,o,free-.016,free+.016,z0+.98,z0+1.16,-.245,-.205,conf,v.IRON)


def carriage_doors(b, o, detail):
    from archetypes import masonry_house_v4_detail as v
    if detail.get('carriage_leaves'):
        boarded_leaves(b,o,detail['carriage_leaves'])
        return
    a,c,z0,z1 = o['u0'],o['u1'],o['z0'],o['z1']
    conf=1.0
    board_top=detail['door_board_top']
    cols,rows=detail['door_upper_panes']
    for leaf in range(2):
        la=a+(c-a)*leaf/2+.022;lc=a+(c-a)*(leaf+1)/2-.022
        # Upper panes remain transparent: no full-height wooden backing card.
        count=detail['door_boards_per_leaf']
        for i in range(count):
            l=la+(lc-la)*i/count;r=la+(lc-la)*(i+1)/count
            v.slab(b,o,l+.0025,r-.0025,z0+.025,board_top,-.30,-.245,conf,v.WOOD)
        frame=.070
        lo=board_top+.09;hi=z1-.11;left=la+frame;right=lc-frame
        v.interior_recess(b,[(left,lo),(right,lo),(right,hi),(left,hi)],
            lambda u,z,off:v.legacy._plane_point(o,u,z,off),v.legacy._plane_dir(o),front=-.30)
        v.glass_pane(b,[v.legacy._plane_point(o,u,z,-.285) for u,z in
                       [(left,lo),(right,lo),(right,hi),(left,hi)]],v.legacy._plane_dir(o),conf)
        for l,r,bot,top in [(la,la+frame,z0+.025,z1-.025),
                            (lc-frame,lc,z0+.025,z1-.025),
                            (la,lc,z0+.025,z0+.13),(la,lc,board_top-.055,lo),
                            (la,lc,z1-.11,z1-.025)]:
            v.slab(b,o,l,r,bot,top,-.30,-.18,conf,v.WOOD)
        for col in range(1,cols):
            x=left+(right-left)*col/cols
            v.slab(b,o,x-.017,x+.017,lo,hi,-.29,-.205,conf,v.WOOD)
        for row in range(1,rows):
            z=lo+(hi-lo)*row/rows
            v.slab(b,o,left,right,z-.025,z+.025,-.29,-.195,conf,v.WOOD)
        # Modest, unornamented hardware; stock sizes are reconstruction.
        hinge=la+.09 if leaf==0 else lc-.09
        for z in [z0+.50,board_top-.30]:
            v.slab(b,o,hinge-.06,hinge+.06,z-.026,z+.026,-.24,-.155,conf,v.IRON)
        handle=lc-.16 if leaf==0 else la+.16
        v.slab(b,o,handle-.018,handle+.018,z0+1.10,z0+1.30,-.19,-.13,conf,v.IRON)


def loft_opening(b,o,detail):
    from archetypes import masonry_house_v4_detail as v
    a,c,z0,z1=o['u0'],o['u1'],o['z0'],o['z1'];w=detail['loft_frame']
    shut=detail.get('loft_door')
    if shut:
        # T-3564 (owner, 2026-11-12, photograph 12): the high door over the
        # carriage doors is shut and painted, "that green should be what is
        # represented": a casing, a head board and one boarded leaf set back.
        reduced=getattr(b,'reduced_sash',False)
        for l,r,lo,hi in [(a,a+w,z0,z1),(c-w,c,z0,z1),(a,c,z0,z0+w),(a,c,z1-w,z1)]:
            v.slab(b,o,l,r,lo,hi,-.30,-.18,1.0,v.PAINTED_WOOD)
        hb=shut['head_board_m']
        v.slab(b,o,a+w,c-w,z1-w-hb,z1-w,-.29,-.20,1.0,v.PAINTED_WOOD)
        st=shut['stile_m']
        lo,hi=z0+w,z1-w-hb;l,r=a+w,c-w
        for sl,sr,sb,stp in [(l,l+st,lo,hi),(r-st,r,lo,hi),(l,r,hi-st,hi),(l,r,lo,lo+st)]:
            v.slab(b,o,sl,sr,sb,stp,-.29,-.235,1.0,v.PAINTED_WOOD)
        diagonal_boards(b,o,l+st,r-st,lo+st,hi-st,-.25,shut,reduced)
        return
    # A loft aperture, not a domestic sash with a meeting rail and linen shade.
    leaves=detail.get('loft_leaves')
    depth=-1.10
    if leaves:
        span=(c-a-2*w)/2
        depth=min(depth,-.30-span-.08)
    v.interior_recess(b,[(a+w,z0+w),(c-w,z0+w),(c-w,z1-w),(a+w,z1-w)],
        lambda u,z,off:v.legacy._plane_point(o,u,z,off),v.legacy._plane_dir(o),
        front=-.29,back=depth)
    for l,r,bot,top in [(a,a+w,z0,z1),(c-w,c,z0,z1),
                        (a,c,z0,z0+w),(a,c,z1-w,z1)]:
        v.slab(b,o,l,r,bot,top,-.30,-.18,1.0,v.WOOD)
    if leaves:
        loft_leaves(b,o,a+w,c-w,z0+w,z1-w,span,leaves)


def loft_leaves(b,o,a,c,lo,hi,span,d):
    """The loft door's two board leaves, hung on the frame and standing open
    inward against the reveals (T-2207). HABS data p. 2 has the loft door
    'closed up' in 1946, so a door hung here before; its leaves, boards and
    strap hinges are reconstructed (docs/LIBERTIES.md L-glessner-cupola-2207).
    """
    from archetypes import masonry_house_v4_detail as v
    conf=1.0;t=d['thickness'];count=d['boards_per_leaf'];gap=.012
    top,bottom=hi-.015,lo+.015
    for side in (0,1):
        # Each leaf lies square to the wall, a hand's breadth off the reveal.
        u0,u1=(a+gap,a+gap+t) if side==0 else (c-gap-t,c-gap)
        for i in range(count):
            near=-.30-span*i/count-.0025;far=-.30-span*(i+1)/count+.0025
            v.slab(b,o,u0,u1,bottom,top,far,near,conf,v.WOOD)
        face=(u1+.006,u1+.014) if side==0 else (u0-.014,u0-.006)
        for z in (bottom+.22,top-.22):
            v.slab(b,o,face[0],face[1],z-.03,z+.03,-.30-span*.72,-.31,conf,v.IRON)


def rough_stone(b,plane,poly,seed):
    from archetypes import masonry_house_v4_detail as v
    # Set above the field's maximum 70 mm rock face, so underlying courses
    # cannot pop through these monolithic lintels and radial voussoirs.
    v.solid_polygon(b,plane,poly,.058,.085,1.0,v.GRANITE)
    def point(q,off):return v.legacy._plane_point(plane,q[0],q[1],off+.095)
    b.block(poly,point,v.legacy._plane_dir(plane),1.0,v.GRANITE,random.Random(seed))


def stable_fabric(b,p):
    from archetypes import masonry_house_v4_detail as v
    d=p.detail.get('north_stable_fabric')
    if not d:return
    pl=d['plane']
    for i,s in enumerate(d['lintels']):
        a,c=s['u'];lo,hi=s['z']
        rough_stone(b,pl,[(a,lo),(c,lo),(c,hi),(a,hi)],19990+i)
    s=d['relieving_arch'];a,c=s['u'];mid=(a+c)/2;half=(c-a)/2
    radius=(half*half+s['rise']**2)/(2*s['rise'])
    center=s['spring']+s['rise']-radius
    theta=math.atan2(radius-s['rise'],half)
    count=s['voussoirs'];outer=radius+s['ring']
    for i in range(count):
        start=theta+(math.pi-2*theta)*i/count+.002
        end=theta+(math.pi-2*theta)*(i+1)/count-.002
        poly=[(mid+rad*math.cos(ang),center+rad*math.sin(ang)) for rad,ang in
              [(radius,start),(outer,start),(outer,end),(radius,end)]]
        rough_stone(b,pl,poly,20000+i)
    h=d['hoist_stone'];a,c=h['u'];lo,hi=h['z'];depth=h['projection']
    # The nose stands 0.6 of the stone's height unless the record reads its
    # own depth (T-3030: the Cornell view's end face, about 0.83 ft).
    under=hi-h['nose'] if 'nose' in h else lo+(hi-lo)*.40
    back=[v.legacy._plane_point(pl,u,z,.065) for u,z in
          [(a,lo),(c,lo),(c,hi),(a,hi)]]
    front=[v.legacy._plane_point(pl,u,z,depth) for u,z in
           [(a,under),(c,under),(c,hi),(a,hi)]]
    v.solid_polygon(b,pl,[(a,lo),(c,lo),(c,hi),(a,hi)],0,.067,1.0,v.GRANITE)
    b.raw(front,1.0,v.GRANITE,v.legacy._plane_dir(pl))
    for i in range(4):
        j=(i+1)%4;b.raw([back[i],back[j],front[j],front[i]],1.0,v.GRANITE)
    drop=h.get('hook_drop')
    if drop:
        # An iron eye under the corbel's nose and the hook a tackle hung from
        # (T-2207); the stone is HABS's, the ironwork reconstructed.
        mid=(a+c)/2;nose=depth-.10
        v.slab(b,pl,mid-.012,mid+.012,under-drop*.55,under,nose-.012,nose+.012,1.0,v.IRON)
        # A square loop of bar: the rails end inside the stiles and the stiles
        # inside the rails, so no two bar faces lie in one plane.
        zt,zb=under-drop*.55,under-drop
        for z in (zt,zb):
            v.slab(b,pl,mid-.065,mid+.065,z-.011,z+.011,nose-.008,nose+.008,1.0,v.IRON)
        for u in (mid-.06,mid+.06):
            v.slab(b,pl,u-.011,u+.011,zb-.008,zt+.008,nose-.011,nose+.011,1.0,v.IRON)


def porch_cheek(b,d,landing):
    from archetypes import masonry_house_v4_detail as v
    a,c=d['cheek_x'];yf=d['front_y'];lo=d['cheek_top'];hi=d['cheek_cap_top']
    # HABS sheet 5 draws real ashlar below one deep coping with a rounded end.
    old=b.decorate;openings=b.openings;b.decorate=True
    # The low cheek occupies the porch aperture. Cutting that same arch out
    # of it would remove its front face instead of building the stone barrier.
    b.openings=[o for o in openings if o.get('style')!='north_entry_alcove']
    v.legacy._box(b,a,yf-d['cheek_depth'],landing,c,yf+.025,lo,1.0,v.GRANITE)
    b.decorate=old;b.openings=openings
    r=min(d['cheek_corner_radius'],hi-lo)
    left=a-.025;right=c+.025
    poly=[(left,lo),(right,lo),(right,hi),(left+r,hi)]
    for i in range(1,9):
        theta=math.pi/2+math.pi/2*i/8
        poly.append((left+r+r*math.cos(theta),hi-r+r*math.sin(theta)))
    plane={'axis':'y','sign':1,'at':yf}
    v.solid_polygon(b,plane,poly,-d['cheek_depth']-.035,.075,1.0,v.GRANITE)
    if d.get('cheek_plaque'):
        cheek_plaque(b,d['cheek_plaque'],plane,left,lo,hi,.075)


# Old-style figures for an address plate, as strokes in a unit box (x 0..0.6, y 0..1):
# each stroke a polyline the plate raises as a narrow fillet.
def _arc(cx,cy,rx,ry,a0,a1,n=6):
    return [(cx+rx*math.cos(math.radians(a0+(a1-a0)*i/n)),cy+ry*math.sin(math.radians(a0+(a1-a0)*i/n))) for i in range(n+1)]
FIGURES={
    '3':[_arc(.3,.76,.24,.22,150,-90)+_arc(.3,.29,.27,.27,90,-155)],
    '5':[[(.52,.98),(.12,.98),(.08,.56)],_arc(.3,.31,.27,.29,140,-150)],
}


def cheek_plaque(b,spec,plane,end_u,lo,hi,face):
    """T-3564: the bronze address plate on the street face of the entry cheek's coping, as
    the owner photographed it (photograph 8): a small dark plate just in from the rounded
    end, its raised border and figures. The figures are drawn as raised fillets."""
    from archetypes import masonry_house_v4_detail as v
    w,h=spec['width_m'],spec['height_m'];t=spec['thick_m'];relief=spec['relief_m']
    cu=end_u+spec['from_end_m'];cz=hi-spec['below_top_m']
    u0,u1,z0,z1=cu-w/2,cu+w/2,cz-h/2,cz+h/2
    mat=v.IRON
    v.slab(b,plane,u0,u1,z0,z1,face,face+t,1.0,mat)
    if getattr(b,'reduced_sash',False):
        return
    front=face+t;rim=spec['rim_m']
    for a,c,lo_,hi_ in ((u0,u1,z1-rim,z1),(u0,u1,z0,z0+rim),(u0,u0+rim,z0+rim,z1-rim),(u1-rim,u1,z0+rim,z1-rim)):
        v.slab(b,plane,a,c,lo_,hi_,front,front+relief,1.0,mat)
    text=spec['text'];fh=h*.62;fw=fh*.6;gap=fh*.18;stroke=fh*.11
    total=len(text)*fw+(len(text)-1)*gap
    x=cu-total/2;base=cz-fh/2
    # The plate's u runs to the viewer's right when the plane faces +y with u = x reversed:
    # draw figures so they read left to right from the street.
    k=-1 if plane['sign']>0 and plane['axis']=='y' else 1
    for ch in text:
        for line in FIGURES[ch]:
            pts=[(x+fw*px,base+fh*py) for px,py in line]
            if k<0:
                pts=[(2*cu-pu,pz) for pu,pz in pts]
            for (pa,za),(pb,zb) in zip(pts,pts[1:]):
                du,dz=pb-pa,zb-za;L=math.hypot(du,dz) or 1
                nu,nz=-dz/L*stroke/2,du/L*stroke/2
                quad=[(pa-nu,za-nz),(pb-nu,zb-nz),(pb+nu,zb+nz),(pa+nu,za+nz)]
                if (quad[1][0]-quad[0][0])*(quad[2][1]-quad[0][1])-(quad[1][1]-quad[0][1])*(quad[2][0]-quad[0][0])<0:
                    quad.reverse()
                v.solid_polygon(b,plane,quad,front,front+relief,1.0,mat)
        x+=fw+gap
