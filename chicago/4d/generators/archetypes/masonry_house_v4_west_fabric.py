"""T-1999's west stable joinery, bounded by the owner's elevation.

These are recessed dark service lights with fine leadwork, not domestic sash
with white roller shades. The dormer has no structural center post.
"""
from __future__ import annotations


def stable_window(b, o):
    from archetypes import masonry_house_v4_detail as v
    a,c,z0,z1=o['u0'],o['u1'],o['z0'],o['z1'];conf=1.0
    dormer=o.get('style')=='west_hood_clear'
    frame=.047 if dormer else .035
    outline=[(a,z0),(c,z0),(c,z1),(a,z1)]
    front=[v.legacy._plane_point(o,u,z,.005) for u,z in outline]
    back=[v.legacy._plane_point(o,u,z,-.245) for u,z in outline]
    for i in range(4):
        j=(i+1)%4
        b.raw([front[i],back[i],back[j],front[j]],conf,v.PAINTED_WOOD if dormer else v.GRANITE)
    v.interior_recess(b,[(a+frame,z0+frame),(c-frame,z0+frame),
                        (c-frame,z1-frame),(a+frame,z1-frame)],
        lambda u,z,off:v.legacy._plane_point(o,u,z,off),v.legacy._plane_dir(o),front=-.25,back=-.85)
    v.slab(b,o,a+frame,c-frame,z0+frame,z1-frame,-.26,-.25,conf,v.DARK_GLASS)
    for l,r,lo,hi in [(a,a+frame,z0,z1),(c-frame,c,z0,z1),
                       (a,c,z0,z0+frame),(a,c,z1-frame,z1)]:
        v.slab(b,o,l,r,lo,hi,-.255,-.20,conf,v.PAINTED_WOOD)
    # Fine cames are glass joinery, not a mullion: 8 mm against a 94 mm
    # doubled domestic sash post. No heavy member divides the dormer aperture.
    columns=max(1,round((c-a)/.36));rows=max(2,round((z1-z0)/.37))
    for i in range(1,columns):
        u=a+(c-a)*i/columns
        v.slab(b,o,u-.004,u+.004,z0+frame,z1-frame,-.247,-.235,conf,v.IRON)
    for i in range(1,rows):
        z=z0+(z1-z0)*i/rows
        v.slab(b,o,a+frame,c-frame,z-.004,z+.004,-.247,-.235,conf,v.IRON)
    if not dormer:
        v.slab(b,o,a-.05,c+.05,z0-.055,z0+.005,-.025,.075,conf,v.GRANITE)
