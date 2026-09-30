"""Exposed rough-stone footing of Glessner's brick courtyard stair drum.

Owner image(10), independently visible in the tunnel-facing courtyard image,
shows large rough granite stones at grade. Their upper edge steps down towards
the passage: this is an exposed foundation, not a new smooth ornamental belt.
HABS photograph 05 is partly ivy/shadow-obscured at this point and does NOT
supply a measurable footing height. The 0.12–0.30 m exposed heights, individual
block joints and 8–40 mm relief below are proportional reconstruction from the
modern photograph, carried to 1904 as the surviving masonry treatment. They do
not move the tower, grade datum, window openings or roof.

The existing resolved stair-tower centre, radius and base elevation control the
geometry; only its exposed courtyard arc receives stone. No photographic pixels
are used. One call to ``stair_tower_plinth(builder, params)`` adds this detail.
"""
from __future__ import annotations

import math
import random

MORTAR=9
ROUGH_STONE=24


def stair_tower_plinth(b, params):
    tower=next((t for t in params.towers if t['name']=='stair'),None)
    if not tower:
        return
    cx,cy,r=tower['cx'],tower['cy'],tower['r']
    base=tower['z0']
    conf=params.detail.get('conf',tower['conf_wall'])
    # The eastern half is embedded in the east wing. The courtyard-facing
    # half and its short returns are visible beside the documented passage.
    start,end=math.radians(80),math.radians(280)
    heights=(.30,.30,.29,.18,.17,.12)
    step=(end-start)/len(heights)
    gap=.007/r

    def P(angle,off,z):
        return cx+(r+off)*math.cos(angle),cy+(r+off)*math.sin(angle),z

    for index,height in enumerate(heights):
        rng=random.Random(1887+index*307)
        lo,hi=start+index*step,start+(index+1)*step
        a,c=lo+gap,hi-gap
        n=8
        # Backing covers the existing thin brick relief at the exposed foot.
        # Its narrow gaps read as mortar rather than brick-coloured joints.
        for j in range(n):
            aa=lo+(hi-lo)*j/n;cc=lo+(hi-lo)*(j+1)/n
            mid=(aa+cc)/2
            b.raw([P(aa,.008,base-.025),P(cc,.008,base-.025),
                   P(cc,.008,base+height),P(aa,.008,base+height)],
                  conf,MORTAR,(math.cos(mid),math.sin(mid),0))

        grid={}
        for j in range(n+1):
            angle=a+(c-a)*j/n
            for k in range(3):
                z=base-.022+(height+.022)*k/2
                edge=j in (0,n) or k in (0,2)
                off=.016+rng.uniform(0,.008) if edge else .022+rng.uniform(0,.018)
                if k==1:
                    z+=rng.uniform(-.018,.018)
                grid[j,k]=(angle,off,z)

        for j in range(n):
            want=(math.cos(a+(c-a)*(j+.5)/n),math.sin(a+(c-a)*(j+.5)/n),0)
            for k in range(2):
                pts=[grid[j,k],grid[j+1,k],grid[j+1,k+1],grid[j,k+1]]
                b.raw([P(*q) for q in pts],conf,ROUGH_STONE,want)
            # A small rough top return meets the unchanged cylindrical brick.
            p,q=grid[j,2],grid[j+1,2]
            b.raw([P(p[0],-.004,p[2]),P(p[0],p[1],p[2]),
                   P(q[0],q[1],q[2]),P(q[0],-.004,q[2])],
                  conf,ROUGH_STONE,(0,0,1))
        for j,sign in ((0,-1),(n,1)):
            for k in range(2):
                p,q=grid[j,k],grid[j,k+1]
                b.raw([P(p[0],.008,p[2]),P(p[0],p[1],p[2]),
                       P(q[0],q[1],q[2]),P(q[0],.008,q[2])],
                      conf,ROUGH_STONE,(-sign*math.sin(p[0]),sign*math.cos(p[0]),0))
