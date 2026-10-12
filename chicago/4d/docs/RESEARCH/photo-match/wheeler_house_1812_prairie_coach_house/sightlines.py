#!/usr/bin/env python3
"""T-2371: can any of the four 'looking south on Prairie from 18th Street' pictures see the
1812 Prairie coach house at all?

    python3 docs/RESEARCH/photo-match/wheeler_house_1812_prairie_coach_house/sightlines.py

Reads the two committed records (data/structures/glessner_house.json and
wheeler_house_1812_prairie_coach_house.json) and the coach house's committed GLB, and sweeps
every camera position the pictures allow. Nothing here is a fitted camera: the sweep is the
whole region the pictures put the photographer in, so the answer does not rest on a solve.

Frame: Glessner's footprint frame (u east, v north, metres; origin the SW corner of its
bounding box), both records placed from their utm_e / utm_n / rotation_deg.

THE OCCLUDER is deliberately the weakest Glessner the record allows: its footprint polygon
extruded only to the lowest eave the record states (the 18th Street cornice, 22.6 ft), with
no roof. Every ridge it has (34.1 to 45.7 ft) would only hide more.

THE TARGET is the coach house's whole GLB bounding box (it is larger than its footprint:
it carries the yard and apron), sampled every metre over its top and its four sides.

THE CAMERA REGION, from what every one of the four prints shows (they are one negative):
  - Glessner's north face is seen, so the eye is north of it: v > 22.555.
  - Glessner's Prairie face recedes on the right, so the eye is east of it: u > 49.149.
  - the photographer stands on the west walk of Prairie, at or north of 18th Street:
    swept generously, u 49.5 to 62 m (the Prairie lot line is 53.63), v 23 to 140 m,
    eye 1.2 to 2.5 m over grade.
Exit 0 and prints "hidden" when no sample of the coach house is in sight from any of them.
"""
import json, math, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FT = 0.3048

def phase(sid):
    d = json.loads((ROOT / 'data/structures' / f'{sid}.json').read_text())
    return d['phases'][0]

def glb_box(path):
    b = path.read_bytes(); n = struct.unpack_from('<I', b, 12)[0]
    j = json.loads(b[20:20 + n]); mn = [1e9] * 3; mx = [-1e9] * 3
    def walk(i, t):
        nd = j['nodes'][i]; tt = [t[k] + (nd.get('translation') or [0, 0, 0])[k] for k in range(3)]
        assert not (nd.get('rotation') or nd.get('scale') or nd.get('matrix')), 'rotated node: read the mesh instead'
        if 'mesh' in nd:
            for p in j['meshes'][nd['mesh']]['primitives']:
                a = j['accessors'][p['attributes']['POSITION']]
                for k in range(3): mn[k] = min(mn[k], a['min'][k] + tt[k]); mx[k] = max(mx[k], a['max'][k] + tt[k])
        for c in nd.get('children', []): walk(c, tt)
    for r in j['scenes'][j.get('scene', 0)]['nodes']: walk(r, [0, 0, 0])
    return mn, mx

def to_frame(base, pos):
    """A point given in `pos`'s footprint frame -> a function into `base`'s frame."""
    def f(u, v):
        th = math.radians(pos['rotation_deg'])        # bearing: the frame is turned clockwise
        e = pos['utm_e'] + u * math.cos(th) + v * math.sin(th)
        n = pos['utm_n'] - u * math.sin(th) + v * math.cos(th)
        tb = math.radians(base['rotation_deg']); de, dn = e - base['utm_e'], n - base['utm_n']
        return de * math.cos(tb) - dn * math.sin(tb), de * math.sin(tb) + dn * math.cos(tb)
    return f

def seg_poly_heights(p, q, poly):
    """Parameters t in (0,1) where segment p->q crosses the polygon's edges."""
    ts = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        d1 = (q[0] - p[0], q[1] - p[1]); d2 = (b[0] - a[0], b[1] - a[1])
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-12: continue
        t = ((a[0] - p[0]) * d2[1] - (a[1] - p[1]) * d2[0]) / den
        s = ((a[0] - p[0]) * d1[1] - (a[1] - p[1]) * d1[0]) / den
        if 0 < t < 1 and 0 <= s <= 1: ts.append(t)
    return ts

# What the Flinn plate (2000 x 1431 px; the picture area x 105..1780, y 75..1290) itself
# measures, read on the plate at 1:1 (README.md here says where):
Y_H = 727        # horizon: vanishing point of the west walk's two edges (x 1032)
X_VP = 1032
NE_X, NE_Y = 1422, 855   # Glessner's NE corner, and the foot of its north face there
FRAME = (105, 1780, 75, 1290)

def main():
    g = phase('glessner_house'); c = phase('wheeler_house_1812_prairie_coach_house')
    poly = g['footprint']['polygon']
    ne = (49.149, 22.555)                             # Glessner's NE corner, its own frame
    eave = 22.6 * FT                                  # the lowest eave Glessner's record states
    mn, mx = glb_box(ROOT / 'assets/gltf/wheeler_house_1812_prairie_coach_house__as_standing_1904.glb')
    cf = to_frame(g['position'], c['position'])
    # coach-house samples: GLB box (x = u, y = height, z = -v), top and four sides, every metre
    us = [mn[0] + i for i in range(int(mx[0] - mn[0]) + 1)] + [mx[0]]
    vs = [-mx[2] + i for i in range(int(mx[2] - mn[2]) + 1)] + [-mn[2]]
    hs = [max(0.0, mn[1]) + i for i in range(int(mx[1] - max(0.0, mn[1])) + 1)] + [mx[1]]
    pts = [(u, v, mx[1]) for u in us for v in vs]
    pts += [(u, v, h) for h in hs for u in us for v in (vs[0], vs[-1])]
    pts += [(u, v, h) for h in hs for v in vs for u in (us[0], us[-1])]
    pts = [(*cf(u, v), h) for u, v, h in pts]
    # THE SWEEP. A level camera (the print's verticals are vertical) at eye height H looking
    # along Prairie: its distance north of Glessner's north face and its focal length are tied
    # by the one fact the plate fixes, that the face's foot at the NE corner lies NE_Y - Y_H px
    # under the horizon: depth = f * H / (NE_Y - Y_H). The NE corner's x then fixes the eye's
    # offset east of the face. So each (H, depth, principal-point x) is one whole camera.
    cams = inframe = seen = 0; best = None; fs = []; margin = None
    for H in (1.2, 1.4, 1.6, 1.8, 2.0, 2.5):
        for depth in range(1, 121):                   # metres north of the NE corner
            f = depth * (NE_Y - Y_H) / H
            for cx in (500, 700, 942, 1200, 1400):     # the print's centre is 942
                # the camera's heading: Prairie's southward line vanishes at X_VP
                a = math.atan2(X_VP - cx, f)          # the axis is turned this far east of south
                lat = depth * math.tan(math.atan2(NE_X - cx, f) - a)   # NE corner west of the eye
                eye = (ne[0] + lat, ne[1] + depth)
                # the photographer is on Prairie's west walk: east of Glessner's face, west of
                # the carriageway (the Prairie lot line is u 53.63; the parkway trees ~ u 58)
                if not 49.5 <= eye[0] <= 62.0: continue
                cams += 1; fs.append(f)
                for (x, y, h) in pts:
                    dx, dy = eye[0] - x, eye[1] - y   # west, south of the eye (both > 0 here)
                    ang = math.atan2(dx, dy) + a      # right of the axis
                    if ang >= math.pi / 2: continue
                    zz = math.hypot(dx, dy) * math.cos(ang)
                    px = cx + f * math.tan(ang); py = Y_H - f * (h - H) / zz
                    inside = FRAME[0] <= px <= FRAME[1] and FRAME[2] <= py <= FRAME[3]
                    inframe += inside
                    ts = seg_poly_heights(eye, (x, y), poly)
                    if any(H + (h - H) * t <= eave for t in ts): continue
                    # it clears the prism: how far outside the print's right edge does it land?
                    if not inside:
                        if px > FRAME[1] and (margin is None or px - FRAME[1] < margin[0]):
                            margin = (px - FRAME[1], H, depth, cx, round(f))
                        continue
                    seen += 1; best = best or (H, depth, cx, round(f), eye, (x, y, h), px, py)
    print(f'sightlines: {len(pts)} samples of the coach house (its GLB box u {mn[0]:.2f}..{mx[0]:.2f}, up to {mx[1]:.2f} m), '
          f'{cams} cameras on the west walk (eye 1.2..2.5 m, 1..120 m north of Glessner, principal x 500..1400 px, '
          f'focal {min(fs):.0f}..{max(fs):.0f} px)')
    print(f'sightlines: {inframe} of {cams * len(pts)} camera-sample pairs fall inside the print; '
          f'{seen} of those clear Glessner taken as a bare {eave:.2f} m prism')
    if margin:
        print(f'sightlines: the nearest sample that would clear the bare prism lands {margin[0]:.0f} px beyond the print\'s '
              f'right edge (eye {margin[1]} m, {margin[2]} m north of Glessner, principal x {margin[3]}, focal {margin[4]} px); '
              f'and that is with every roof of Glessner left off')
    if seen:
        print(f'sightlines: VISIBLE from {best}'); return 1
    print('sightlines: hidden — from every camera the plate allows, each sample of the coach house is outside the print or behind Glessner')
    return 0

if __name__ == '__main__':
    sys.exit(main())
