"""North stable joinery and masonry reconstructed from the supplied NW view.

HABS owns the apertures; the data record owns the bounded fabric dimensions.
The photo's date is not established, so this 1904 treatment is reconstructed.
No photograph is sampled into a texture and no measured doorway is widened.
"""
from __future__ import annotations

import math
import random


def carriage_doors(b, o, detail):
    from archetypes import masonry_house_v4_detail as v
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
    # A loft aperture, not a domestic sash with a meeting rail and linen shade.
    v.interior_recess(b,[(a+w,z0+w),(c-w,z0+w),(c-w,z1-w),(a+w,z1-w)],
        lambda u,z,off:v.legacy._plane_point(o,u,z,off),v.legacy._plane_dir(o),
        front=-.29,back=-1.10)
    for l,r,bot,top in [(a,a+w,z0,z1),(c-w,c,z0,z1),
                        (a,c,z0,z0+w),(a,c,z1-w,z1)]:
        v.slab(b,o,l,r,bot,top,-.30,-.18,1.0,v.WOOD)


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
    back=[v.legacy._plane_point(pl,u,z,.065) for u,z in
          [(a,lo),(c,lo),(c,hi),(a,hi)]]
    front=[v.legacy._plane_point(pl,u,z,depth) for u,z in
           [(a,lo+(hi-lo)*.40),(c,lo+(hi-lo)*.40),(c,hi),(a,hi)]]
    v.solid_polygon(b,pl,[(a,lo),(c,lo),(c,hi),(a,hi)],0,.067,1.0,v.GRANITE)
    b.raw(front,1.0,v.GRANITE,v.legacy._plane_dir(pl))
    for i in range(4):
        j=(i+1)%4;b.raw([back[i],back[j],front[j],front[i]],1.0,v.GRANITE)


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
