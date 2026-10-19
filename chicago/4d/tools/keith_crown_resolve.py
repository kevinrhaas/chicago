#!/usr/bin/env python3
"""T-2813: re-solve the five cameras fitted on Keith's crown when the crown moves.

Five of keith_house_1808_prairie's reference views are fitted, in part, on points of the crown
(the pinnacle apexes, the lattice's coping and openings), each read in the picture against the
model's own point. When the wall head moves those model points move with it and the pixels they
were read at do not, so every such camera has to be re-solved on the moved points or it draws the
crown where the model used to be. T-2680 did this by hand when the crown came down 0.2 m; T-2813
takes 0.16 m more out of the moulded course under the lattice (wall_head.depth_m), and this is
that re-solve as a tool, so the next move re-runs it.

The controls are the views' own, as their `solve` states them: the points and lines below were
read at the wall head of 15.0 m, and a crown control (CROWN) is carried by the record's wall head
now (principal floor + storey heights). Each camera keeps the model its last solve fitted: the
same parameters free and the rest held (eye height 1.7 m, cx, and roll on the level cameras, f on
the Glessner plate), started from the committed camera. The c. 1888 view's two lines are the
lattice's opening rows (perpendicular distance, as T-2748 read them), and owner-1800, a crop of
the same photograph, is carried onto its re-fitted camera through the SIFT map T-2748 states.

  python3 tools/keith_crown_resolve.py            # print the fits
  python3 tools/keith_crown_resolve.py --write    # and write the cameras and their solve notes

Read before trusting: the residuals are the controls' own, so a camera that fitted well on the
old crown and badly on the new one says the crown moved against that picture.
"""
from pathlib import Path
import argparse, json, math, re
import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
SID = 'keith_house_1808_prairie'
VIEWS = ROOT / 'data/reference_views' / SID
READ_AT_E = 15.0          # the wall head the controls below were read against (T-2680's)
TAG = 'T-2813 re-solve:'
C = 'crown'

# view -> free parameters, and the controls: (world [u, v, y], (px, py) with None free, crown?)
FITS = {
    'a18-gh-glessner-front-with-keith': {'free': ['u', 'v', 'yaw', 'f', 'cy'], 'points': [
        ([17.86, 10.252, 17.07], (129.5, 7), C), ([12.729, 10.18, 17.268], (235, 146.5), C),
        ([18, 9.96, 15.66], (102, None), C), ([18, 9.535, 15.67], (72, None), C), ([18, 9.11, 15.69], (42, None), C)]},
    'a18-gh-florian-1948-northeast-overall': {'free': ['u', 'v', 'yaw', 'f', 'cy'], 'points': [
        ([17.86, 10.252, 17.07], (237.5, 160.6), C), ([12.729, 10.18, 17.268], (342.5, 200), C),
        ([17.873, 8.244, 12.634], (159, 362.5), None), ([17.9, 8.24, 10.45], (159, 455), None),
        ([17.885, 7.679, 12.677], (131, 362.5), None), ([17.968, 9.578, 16.11], (214, 197.5), C)]},
    'a18-inland-architect-1888-02-glessner-plate': {'free': ['u', 'v', 'yaw', 'roll', 'cy'], 'points': [
        ([17.86, 10.252, 17.07], (1093.6, 580), C), ([12.729, 10.18, 17.268], (1060.5, 682.3), C),
        ([17.873, 8.244, 12.634], (914.4, 514.6), None), ([17.9, 8.24, 10.45], (836, 514.6), None),
        ([17.885, 7.679, 12.677], (914.4, 495.4), None)]},
    'a18-rba-reed-1941-prairie-north-from-1820': {'free': ['u', 'v', 'yaw', 'f', 'cy'], 'points': [
        ([17.86, 0.188, 17.07], (306.6, 140), C), ([17.86, 10.252, 17.07], (346.6, 191.6), C),
        ([17.907, 2.553, 12.7], (318.1, 246.3), None), ([17.848, 2.78, 10.562], (318.1, 295.6), None),
        ([18.963, 3.011, 9.074], (333, 324.4), None), ([18.963, 3.134, 6.794], (333, 377), None)]},
    'a18-gh-1800-block-looking-sw-c1888': {'free': ['u', 'v', 'yaw', 'f', 'cy', 'aspect'], 'points': [
        ([17.86, 10.251, 17.07], (1135, 105), C), ([12.73, 10.18, 17.268], (1311, 139), C),
        ([17.86, 0.187, 17.07], (893, 256), C), ([18.0, 10.4, 15.5], (1126, None), None),
        ([18.0, 10.4, 12.0], (1126, None), None), ([17.8, 2.40, 12.60], (935, 438), None),
        ([17.8, 2.40, 10.53], (935, 527), None)],
        # the lattice's upper-row opening tops and lower-row opening bottoms on the front (u 17.72)
        'lines': [(17.72, 15.92, [(1110, 172), (920, 287)]), (17.72, 15.25, [(1110, 205), (920, 321)])]},
}
# owner-1800 is the owner's crop of the c. 1888 photograph: x' = SX x + DX, y' = SY y + DY into it (T-2748)
CROP = {'view': 'a18-owner-1800-block-looking-sw', 'of': 'a18-gh-1800-block-looking-sw-c1888',
        'SX': 2.9369, 'DX': 41.77, 'SY': 2.8971, 'DY': 233.87}


def wall_head():
    form = json.loads((ROOT / f'data/structures/{SID}.json').read_text())['phases'][0]['form']
    return form['principal_floor_m']['value'] + sum(form['storey_heights_m']['value'])


def basis(c):
    if 'basis_right_up_forward' in c:
        return np.array(c['basis_right_up_forward'], float)
    t = math.radians(c['yaw_deg'])
    return np.array([[math.cos(t), -math.sin(t), 0.], [0., 0., 1.], [math.sin(t), math.cos(t), 0.]])


def camera(c, p, free):
    """The committed camera c moved by the free parameters p: eye u, v; a turn about the vertical
    (yaw, degrees, the convention yaw_deg uses); a roll about the forward axis; f, cy, aspect."""
    q = dict(zip(free, p))
    B = basis(c)
    a = math.radians(q.get('yaw', 0.0))
    turn = np.array([[math.cos(a), math.sin(a), 0.], [-math.sin(a), math.cos(a), 0.], [0., 0., 1.]])
    B = B @ turn.T
    r = math.radians(q.get('roll', 0.0))
    right, up, fwd = B
    B = np.array([math.cos(r) * right + math.sin(r) * up, math.cos(r) * up - math.sin(r) * right, fwd])
    eye = np.array(c['eye'], float) + np.array([q.get('u', 0.0), q.get('v', 0.0), 0.0])
    return {'B': B, 'eye': eye, 'f': c['focal_px'] * (1 + q.get('f', 0.0)), 'cx': c['principal_px'][0],
            'cy': c['principal_px'][1] + q.get('cy', 0.0), 'aspect': c.get('pixel_aspect', 1) * (1 + q.get('aspect', 0.0))}


def project(k, P):
    d = np.asarray(P, float) - k['eye']
    right, up, fwd = k['B']
    z = d @ fwd
    return np.array([k['cx'] + k['aspect'] * k['f'] * (d @ right) / z, k['cy'] - k['f'] * (d @ up) / z])


def residuals(k, fit, dE):
    out = []
    for P, px, crown in fit['points']:
        P = [P[0], P[1], P[2] + (dE if crown else 0.0)]
        q = project(k, P)
        out += [q[i] - px[i] for i in (0, 1) if px[i] is not None]
    for u, y, reads in fit.get('lines', ()):
        a, b = project(k, [u, 1.0, y + dE]), project(k, [u, 9.0, y + dE])
        n = np.array([a[1] - b[1], b[0] - a[0]]) / np.hypot(*(b - a))
        out += [float((np.array(r, float) - a) @ n) for r in reads]
    return np.array(out)


def solve(view, fit, dE):
    c = json.loads((VIEWS / f'{view}.json').read_text())
    free = fit['free']
    scale = {'u': 1.0, 'v': 1.0, 'yaw': 0.1, 'roll': 0.1, 'f': 0.01, 'cy': 10.0, 'aspect': 0.01}
    before = residuals(camera(c, [0.0] * len(free), free), fit, 0.0)
    moved = residuals(camera(c, [0.0] * len(free), free), fit, dE)
    s = least_squares(lambda p: residuals(camera(c, p, free), fit, dE), [0.0] * len(free),
                      x_scale=[scale[n] for n in free])
    k = camera(c, s.x, free)
    rms = lambda r: float(np.sqrt(np.mean(r ** 2)))
    return c, k, dict(zip(free, s.x)), {'before': rms(before), 'unrefit': rms(moved), 'after': rms(s.fun),
                                        'max': float(np.max(np.abs(s.fun))), 'resid': [round(float(x), 1) for x in s.fun]}


def write(view, c, k, q, r, fit, E, dE):
    yaw = (c['yaw_deg'] + q.get('yaw', 0.0)) % 360
    c['eye'] = [round(float(x), 4) for x in k['eye'][:2]] + [c['eye'][2]]
    c['yaw_deg'] = round(yaw, 4)
    c['focal_px'] = round(k['f'], 3)
    c['principal_px'] = [c['principal_px'][0], round(k['cy'], 3)]
    if 'basis_right_up_forward' in c:
        c['basis_right_up_forward'] = [[round(float(x), 9) for x in row] for row in k['B']]
    if 'pixel_aspect' in c:
        c['pixel_aspect'] = round(k['aspect'], 4)
    held = {'u': 'u', 'v': 'v', 'yaw': 'yaw', 'f': 'f', 'cy': 'cy', 'roll': 'roll', 'aspect': 'pixel_aspect'}
    moved = [P[:2] + [round(P[2] + dE, 3)] for P, _, crown in fit['points'] if crown and P[2] > 16.0]
    note = (f"{TAG} the wall head stands at {E:.2f} m (keith storey_heights_m, wall_head.depth_m), so the crown "
            f"controls stand {-dE:.2f} m under the heights above, read at the same pixels (moved: "
            f"{', '.join(str(m) for m in moved)}{'; the lattice lines at u 17.72 to y ' + ', '.join(f'{y + dE:.2f}' for _, y, _ in fit['lines']) if fit.get('lines') else ''}). "
            f"Same camera model, free: {', '.join(held[n] for n in fit['free'])}; the rest held at the previous solve. "
            f"Per-coordinate residual px {r['resid']}; coordinate RMS {r['after']:.2f} px, max {r['max']:.2f} px "
            f"(the previous camera on the previous controls, counted the same way: {r['before']:.2f} px; on the moved "
            f"controls unrefitted: {r['unrefit']:.2f} px). Re-derived by tools/keith_crown_resolve.py.")
    c['solve'] = re.sub(r' ?' + re.escape(TAG) + r'.*$', '', c['solve']) + ' ' + note
    (VIEWS / f'{view}.json').write_text(json.dumps(c, indent=2, ensure_ascii=False) + '\n')


def carry_crop(E):
    src = json.loads((VIEWS / f"{CROP['of']}.json").read_text())
    c = json.loads((VIEWS / f"{CROP['view']}.json").read_text())
    c['eye'], c['yaw_deg'] = src['eye'], src['yaw_deg']
    c['focal_px'] = round(src['focal_px'] / CROP['SY'], 3)
    c['principal_px'] = [round((src['principal_px'][0] - CROP['DX']) / CROP['SX'], 3),
                         round((src['principal_px'][1] - CROP['DY']) / CROP['SY'], 3)]
    c['pixel_aspect'] = round(src['pixel_aspect'] * CROP['SY'] / CROP['SX'], 4)
    note = (f"{TAG} carried again onto the c. 1888 camera as re-solved on the crown at a wall head of {E:.2f} m, "
            f"through the same map (tools/keith_crown_resolve.py).")
    c['solve'] = re.sub(r' ?' + re.escape(TAG) + r'.*$', '', c['solve']) + ' ' + note
    (VIEWS / f"{CROP['view']}.json").write_text(json.dumps(c, indent=2, ensure_ascii=False) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help='write the re-solved cameras into their view files')
    args = ap.parse_args()
    E = wall_head()
    dE = E - READ_AT_E
    print(f'wall head {E:.3f} m: crown controls move {dE:+.3f} m from where they were read')
    for view, fit in FITS.items():
        c, k, q, r = solve(view, fit, dE)
        print(f"{view:46s} RMS {r['before']:.2f} px as committed, {r['unrefit']:.2f} on the moved crown, "
              f"{r['after']:.2f} re-solved (max {r['max']:.2f}); "
              + ', '.join(f'{n} {x:+.4g}' for n, x in q.items()))
        if args.write:
            write(view, c, k, q, r, fit, E, dE)
    if args.write:
        carry_crop(E)
        print(f"wrote {len(FITS)} cameras and carried {CROP['view']}")


if __name__ == '__main__':
    main()
