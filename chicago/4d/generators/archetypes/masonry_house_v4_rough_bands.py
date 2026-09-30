"""Rock-faced curved tower belts for the opt-in Glessner v4 builder.

HABS courtyard photo05 and the supplied courtyard close views support rough stone
in both lantern belts. Their exact joints and fractures are reconstructed. The
caller owns the radius and vertical endpoints: this helper only subdivides their
existing envelope. It does not add a cornice or enlarge the tower.
"""
from __future__ import annotations

import math
import random

GRANITE, MORTAR, ROUGH_TRIM = 0, 9, 24


def add_rough_band(b, cx, cy, outer_radius, z0, z1, confidence):
    """One curved stone course, bounded by the supplied radius and z endpoints.

    Production ``b.block`` provides angular split faces. Its 4–70 mm relief is
    compressed into the outer 40 mm of the existing belt, keeping every point
    inside its former smooth drum. A 15 mm dressed top seat and closed annular
    top/bottom edges retain its silhouette; they use the same granite fabric.
    """
    if outer_radius <= .10 or z1 <= z0:
        raise ValueError("A curved stone belt needs a positive radius and height")
    face_radius = outer_radius - .040
    bed_radius = face_radius - .012
    circumference = 2 * math.pi * face_radius
    seat = min(.015, (z1-z0) * .12)
    joint = .012
    count = max(8, round(circumference / .65))
    seed = round((cx*11 + cy*23 + z0*31) * 1000)
    widths_rng = random.Random(seed)
    weights = [widths_rng.uniform(.88, 1.12) for _ in range(count)]
    weight_sum = sum(weights)

    def point(q, off):
        angle = q[0] / face_radius
        radius = face_radius + max(-.009, min(.070, off)) * (.040/.070)
        return (cx+radius*math.cos(angle), cy+radius*math.sin(angle), q[1])

    def circle(radius, angle, z):
        return (cx+radius*math.cos(angle), cy+radius*math.sin(angle), z)

    # The old drum had64 angular segments; preserve those circular edge points.
    for i in range(64):
        a = 2*math.pi*i/64
        c = 2*math.pi*(i+1)/64
        normal = (math.cos((a+c)/2), math.sin((a+c)/2), 0)
        b.raw([circle(bed_radius,a,z0),circle(bed_radius,c,z0),
               circle(bed_radius,c,z1-seat),circle(bed_radius,a,z1-seat)],
              confidence,MORTAR,normal)
        b.raw([circle(outer_radius,a,z1-seat),circle(outer_radius,c,z1-seat),
               circle(outer_radius,c,z1),circle(outer_radius,a,z1)],
              confidence,GRANITE,normal)
        for z, facing in ((z0,(0,0,-1)),(z1,(0,0,1))):
            b.raw([circle(bed_radius,a,z),circle(outer_radius,a,z),
                   circle(outer_radius,c,z),circle(bed_radius,c,z)],
                  confidence,GRANITE,facing)

    u = 0.0
    for i, weight in enumerate(weights):
        end = circumference if i == count-1 else u + circumference*weight/weight_sum
        a,c = u+joint/2,end-joint/2
        lo,hi = z0+joint/2,z1-seat-joint/2
        if c>a and hi>lo:
            angle = (a+c)/(2*face_radius)
            polygon = [(a,lo),(c,lo),(c,hi),(a,hi)]
            b.block(polygon,point,(math.cos(angle),math.sin(angle),0),
                    confidence,ROUGH_TRIM,random.Random(seed+719*i))
        u = end
