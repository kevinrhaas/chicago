"""Raised terracotta ridge collars for Glessner v4.

The repeating crest silhouette is visible in HABS courtyard photo05 (circa1923)
and photo14, and agrees with the supplied modern views. Carrying the roof form
back to1904 is inferred; the collar section and dimensions below are reconstructed.
No photographic pixels are projected onto these shapes.
"""
from __future__ import annotations

import math


def add_ridge_crest(b, axis, ridge_at, ridge_z, lo, hi, confidence, material):
    """Add one integral raised collar within an existing ridge-cap interval.

    Existing caps have140mm radius and sit55mm above the ridge datum. This collar
    adds55mm at the crown, tapering to zero additional width at the shoulders.
    Its35mm axial thickness fits inside the cap; ridge axis, endpoints and roof
    pitches remain unchanged. Exact dimensions are reconstructed, not surveyed.
    """
    if axis not in ('x','y') or hi<=lo:
        return
    width=min(.035,(hi-lo)*.24)
    front=lo+min(.004,(hi-lo)*.02)
    back=min(hi,front+width)
    inner_radius=.138
    segments=12

    def point(angle,along,outer):
        radius=.14+.055*math.sin(angle)**2 if outer else inner_radius
        across=ridge_at+radius*math.cos(angle)
        z=ridge_z+.055+radius*math.sin(angle)
        return (across,along,z) if axis=='y' else (along,across,z)

    axial=(0,1,0) if axis=='y' else (1,0,0)
    for i in range(segments):
        a,c=math.pi*i/segments,math.pi*(i+1)/segments
        m=(a+c)/2
        outward=(math.cos(m),0,math.sin(m)) if axis=='y' else (0,math.cos(m),math.sin(m))
        b.raw([point(a,front,True),point(c,front,True),
               point(c,back,True),point(a,back,True)],confidence,material,outward)
        b.raw([point(a,front,False),point(a,front,True),
               point(c,front,True),point(c,front,False)],
              confidence,material,tuple(-v for v in axial))
        b.raw([point(a,back,False),point(c,back,False),
               point(c,back,True),point(a,back,True)],confidence,material,axial)
    for angle in (0,math.pi):
        b.raw([point(angle,front,False),point(angle,back,False),
               point(angle,back,True),point(angle,front,True)],confidence,material,(0,0,-1))
