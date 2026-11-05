"""T-3373: the small hooded dormer on the north range's courtyard slope.

The owner's aerials show a small tiled, pointed dormer just east of the great
chimney, above the copper lean-to, and HABS photograph 5 (c. 1923) shows a
pointed finial at that place. Its form follows the east wing's courtyard
dormers (HABS sheet 4): a timber front with one light, tile-hung cheeks and a
pyramidal hood with a short kick and a finial. Its size and heights are
reconstructed. All coordinates are metres in the shared building frame
(x east, y north); the dormer looks south into the court.
"""
from __future__ import annotations

import math

from archetypes import masonry_house as legacy
from archetypes.masonry_house_v4_detail import (PAINTED_WOOD, ROOF, aperture, glass_pane,
                                                interior_recess, slab, subtract)
from archetypes.masonry_house_v4_west_roof import slope, z


def spec(params):
    d = params.detail.get('north_court_dormer')
    if not d:
        return None
    north = next(r for r in params.ranges if r['name'] == 'north_range')
    tile = slope('y', north['y0'], north['eave_lo_z'], north['ridge_at'], north['ridge_z'])
    # The cheeks run back until the tiled slope reaches the hood's eave.
    back = d['front_y'] + (d['eave_z'] - z(tile, 0, d['front_y'])) / tile[1]
    return dict(d, tile=tile, back_y=back)


def hood(d):
    """Pyramid over an eave ring with a short kick, as the east wing's dormers."""
    a, c = d['x']
    f, bk, ze = d['front_y'], d['back_y'], d['eave_z']
    o = d['side_overhang_m']
    inner = o - d['side_apron_inset_m']
    ring = [(a-o, f-.30, ze), (c+o, f-.30, ze), (c+o, bk+.10, ze), (a-o, bk+.10, ze)]
    kick = [(a-inner, f-.30+.18, ze+.13), (c+inner, f-.30+.18, ze+.13),
            (c+inner, bk+.10-.18, ze+.13), (a-inner, bk+.10-.18, ze+.13)]
    apex = ((a+c)/2, (f+bk)/2, d['apex_z'])
    faces = []
    for i in range(4):
        j = (i+1) % 4
        faces.extend([[ring[i], ring[j], kick[j], kick[i]], [kick[i], kick[j], apex]])
    return ring, kick, apex, faces


def above_tile(points, d):
    from archetypes.masonry_house_v4_north_tower import _half
    return _half(points, lambda p: p[2]-z(d['tile'], p[0], p[1]))


def tile_holes(params):
    """Plan footprint of tiles enclosed under the hood (its walls' box)."""
    d = spec(params)
    if not d:
        return []
    a, c = d['x']
    return [[(a, d['front_y']), (c, d['front_y']), (c, d['back_y']), (a, d['back_y'])]]


def add(b, params):
    d = spec(params)
    if not d:
        return
    conf = d['conf']
    a, c = d['x']
    f, bk, ze = d['front_y'], d['back_y'], d['eave_z']
    z0 = z(d['tile'], 0, f) - .05
    pl = {'axis': 'y', 'sign': -1, 'at': f}
    normal = legacy._plane_dir(pl)
    lo, hi = d['light']
    margin = (c-a)*d['light_margin_fraction']
    op = {**pl, 'face': 'south', 'kind': 'window', 'u0': a+margin, 'u1': c-margin,
          'z0': lo, 'z1': hi, 'conf': conf}
    for frag in subtract([(a, z0), (c, z0), (c, ze), (a, ze)], [aperture(op)]):
        b.raw([legacy._plane_point(pl, u, h) for u, h in frag], conf, PAINTED_WOOD, normal)
    # Tile-hung cheeks, from the slope up to the hood's eave.
    for u, s in ((a, -1), (c, 1)):
        cheek = above_tile([(u, f, z0), (u, bk, ze-.0), (u, f, ze)], d)
        if cheek and len(cheek) > 2:
            legacy._poly_facing(b, cheek, conf, ROOF, (s, 0, 0))
    # One undivided light in a timber frame, as the east wing's dormers.
    la, lc = op['u0'], op['u1']
    k = d['frame_stock_m']
    outline = aperture(op)
    for p, q in zip(outline, outline[1:]+outline[:1]):
        b.raw([legacy._plane_point(pl, *p, .016), legacy._plane_point(pl, *p, -.20),
               legacy._plane_point(pl, *q, -.20), legacy._plane_point(pl, *q, .016)], 1.0, PAINTED_WOOD)
    inner = [(la+k, lo+k), (lc-k, lo+k), (lc-k, hi-k), (la+k, hi-k)]
    interior_recess(b, inner, lambda u, h, off: legacy._plane_point(pl, u, h, off), normal,
                    front=-.206, back=-.50)
    glass_pane(b, [legacy._plane_point(pl, u, h, -.20) for u, h in inner], normal, 1.0)
    for u0, u1, z0_, z1_ in [(la, la+k, lo, hi), (lc-k, lc, lo, hi), (la, lc, lo, lo+k), (la, lc, hi-k, hi)]:
        slab(b, pl, u0, u1, z0_, z1_, -.195, -.13, 1.0, PAINTED_WOOD)
    slab(b, pl, la-.05, lc+.05, lo-.045, lo+.012, -.07, .07, 1.0, PAINTED_WOOD)
    # The hood, its fascia and soffit, cut where it dies into the slope.
    ring, kick, apex, faces = hood(d)
    for i, face in enumerate(faces):
        kept = above_tile(face, d)
        if kept and len(kept) > 2:
            legacy._up(b, kept, 1.0 if i % 2 == 0 else conf, ROOF)
    fascia = d['fascia_m']
    for p, q in zip(ring, ring[1:]+ring[:1]):
        facing = ((p[0]+q[0])/2-apex[0], (p[1]+q[1])/2-apex[1], 0)
        poly = above_tile([(p[0], p[1], ze-fascia), (q[0], q[1], ze-fascia), q, p], d)
        if poly and len(poly) > 2:
            b.raw(poly, 1.0, PAINTED_WOOD, facing)
    soffit = above_tile([(p[0], p[1], ze-fascia) for p in ring], d)
    if soffit and len(soffit) > 2:
        b.raw(soffit, 1.0, PAINTED_WOOD, (0, 0, -1))
    if params.detail.get('roof_edges'):
        from archetypes.masonry_house_v4_roof_edges import hip_caps
        rim = None
        spec_f = params.detail.get('court_finial')
        if spec_f and 'north_dormer_profile_ft' in spec_f:
            rim = .85*spec_f['north_dormer_profile_ft'][0][1]*.3048
        for p, v in zip(ring, kick):
            top = apex
            reach = math.hypot(v[0]-apex[0], v[1]-apex[1])
            if rim and reach > rim:
                top = tuple(v[h]+(apex[h]-v[h])*(1-rim/reach) for h in range(3))
            for s0, s1 in ((p, v), (v, top)):
                dp, dq = (q[2]-z(d['tile'], q[0], q[1]) for q in (s0, s1))
                if max(dp, dq) <= 0:
                    continue
                if min(dp, dq) < 0:
                    cut = tuple(s0[h]+dp/(dp-dq)*(s1[h]-s0[h]) for h in range(3))
                    s0, s1 = (cut, s1) if dp < 0 else (s0, cut)
                hip_caps(b, s0, s1, .02)
    if params.detail.get('court_finial') and 'north_dormer_base_ft' in params.detail['court_finial']:
        from archetypes.masonry_house_v4_court import court_finial
        court_finial(b, apex[0], apex[1], 'north_dormer', ROOF)
    else:
        legacy._finial(b, apex[0], apex[1], d['apex_z'], .30, 1.0, ROOF)
