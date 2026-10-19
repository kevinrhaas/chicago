#!/usr/bin/env python3
"""T-2830: what makes the 1965 close view of Keith's loggia (a18-gh-1808-porch-1965) draw the loggia
about 1.3 times taller than the model, tested by fit, and a third picture read beside it.

T-2764 fitted this slide with a level camera on the bow's lights and the loggia's plan
(tools/keith_1965_level_fit.py) and found the as-built loggia drawn about 26 % short on it; one free
factor on the loggia's heights over its deck read 1.29-1.32. It left three causes to rule: the
slide's optics, the bow's heights (the camera is fixed on the bow's lights), and the loggia's plan.
This takes T-2764's controls and world points unchanged (its edges, read by luminance profile off
the 675 x 456 slide) and fits all of them, the loggia's heights included, under one hypothesis at a
time, each adding the parameters that hypothesis needs to the level camera's six (eye u and v,
heading, roll, focal length, principal y; the eye 1.7 m over grade unless freed):

  OPTICS      the camera pitched (any verticals' lean), a radial lens or enlarger distortion k1
              about the principal point, the principal point's x freed (a cropped or shifted
              frame), and their combinations;
  THE BOW     the principal lights' heads at a free height (the bow's lights are the camera's
              ruler), or every bow height scaled about grade;
  THE PLAN    the whole loggia moved in plan (du toward the street, dv north), its layout scaled
              about its centre (L), its members' plan size (m: shafts and pair centres) or the
              pedestals' (w);
  HEIGHTS     one factor k on the loggia's heights over its deck (T-2764's), with and without a
              free deck height D under it.

A cause that is the slide's or the model's should take the residual down to the bow-and-plan
camera's own 3.5 px RMS with its parameters inside what the house allows. The table says which do.

The world points were read off GLB 8f38ad90 (T-2765's bow, T-2763's loggia). The GLB in the tree has
since been rebuilt twice, by T-2773 (the bow's coursing: rhythm "street_front" for "alternating")
and T-2811 (the cowl ventilator); neither moves a bow opening or the loggia, so the points stand.
This checks the committed GLB against the one the match record was made from, not against 8f38ad90.

THE THIRD PICTURE. Nickel 1967 (nickel-1967) stands nearly square to the front with a camera fitted
on the flat front's corners only (grade, 15.2 m and the pinnacles; T-1883), so nothing on the bow or
the loggia steered it. Its rows are read here by luminance profile (NICKEL_READS, the columns and
transitions named beside each) and set against the rows its committed camera draws for the as-built
loggia and for the bow's principal sill and string course, both heights read off the 1888 plate
(docs/RESEARCH/photo-match/keith_house_1808_prairie/inland-1888-bow-lights.json). The ratio of the
loggia's column to the bow's sill-to-string-course span, print over camera, is a ratio no distance
or focal length changes, as T-2771 argued for the crown stack.

  python3 tools/keith_1965_cause_fit.py            # print the table
  python3 tools/keith_1965_cause_fit.py --write    # and write REPORT

What it does not do: re-fit or re-pick T-2764's controls, re-fit Nickel's camera, or move the model.
"""
from pathlib import Path
import argparse, hashlib, json, math, sys
import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, str(Path(__file__).resolve().parent))
import keith_1965_level_fit as lf  # noqa: E402  T-2764's controls and world points

ROOT = Path(__file__).resolve().parents[1]
MATCH = ROOT / 'data/reference_views/keith_house_1808_prairie/a18-gh-1808-porch-1965.match.json'
NICKEL = ROOT / 'data/reference_views/keith_house_1808_prairie/nickel-1967.json'
REPORT = ROOT / 'docs/RESEARCH/photo-match/keith_house_1808_prairie/a18-gh-1808-porch-1965-cause-fit.json'
LOGGIA_CENTRE = (20.40, 8.6975)   # between the pairs' centres, v 7.4475 and 9.9475
PAIR_CENTRES = (7.4475, 9.9475)
BOUNDS = {'u': (20, 60), 'v': (-30, 15), 'y': (0.3, 4), 'yaw': (270, 345), 'roll': (-4, 4), 'f': (200, 2500),
          'cy': (50, 600), 'cx': (-1500, 2000), 'pitch': (-30, 30), 'k1': (-1.5, 1.5), 'hh': (3.5, 5.6),
          'kb': (0.6, 1.4), 'du': (-4, 4), 'dv': (-4, 4), 'L': (0.4, 1.6), 'm': (0.5, 1.8), 'w': (0.4, 1.6),
          'k': (0.5, 1.8), 'D': (0.5, 3.0)}
DEFAULT = {'y': 1.7, 'cx': lf.CX, 'pitch': 0.0, 'k1': 0.0, 'hh': 5.30, 'kb': 1.0, 'du': 0.0, 'dv': 0.0,
           'L': 1.0, 'm': 1.0, 'w': 1.0, 'k': 1.0, 'D': lf.DECK}
# (group, label, free parameters beyond the level camera's six)
HYPOTHESES = [
    ('level', 'level camera, every control (T-2764\'s "all controls")', []),
    ('level', 'level camera, eye height free', ['y']),
    ('optics', 'pitched camera', ['pitch']),
    ('optics', 'pitched camera, eye height free', ['pitch', 'y']),
    ('optics', 'radial distortion k1', ['k1']),
    ('optics', 'principal point x free', ['cx']),
    ('optics', 'principal x and k1', ['cx', 'k1']),
    ('optics', 'pitch, k1 and eye height', ['pitch', 'k1', 'y']),
    ('bow', 'principal lights\' heads at a free height', ['hh']),
    ('bow', 'every bow height scaled about grade', ['kb']),
    ('plan', 'loggia moved in plan (du, dv)', ['du', 'dv']),
    ('plan', 'loggia layout scaled about its centre (L)', ['L']),
    ('plan', 'loggia members\' plan size (m)', ['m']),
    ('plan', 'pedestals\' plan size (w)', ['w']),
    ('plan', 'layout and pedestals (L, w)', ['L', 'w']),
    ('heights', 'one factor on the loggia\'s heights (k)', ['k']),
    ('heights', 'k, eye height free', ['k', 'y']),
    ('heights', 'k over a free deck height D', ['k', 'D']),
    ('heights', 'a free deck height D alone', ['D']),
    ('heights', 'k with the heads free', ['k', 'hh']),
    ('heights', 'k with the members\' plan size', ['k', 'm']),
]

# Nickel 1967, rows read by luminance profile (mean across the stated columns, 1 px steps)
NICKEL_READS = {
    'south pair capital top': (623.5, 'x 339-346: the beam\'s shadow ends (y 618-623 dark, 624-631 lit)'),
    'south pedestal cap arris': (696.5, 'x 339-346: the cap\'s shadow line, darkest y 697-698'),
    'bow principal sill': (701.5, 'x 284-298: the glass ends (dark to y 701) on the lit sill (702-709)'),
    'bow string course foot': (620.0, 'x 274-279 and 284-298 alike: the course\'s shadow line, darkest y 620-621'),
    'bow principal glass head': (647.5, 'x 284-298: the glass begins (y 648 onward), stone-pale above it from 623'),
}
PLATE_LEVELS = {'bow principal sill': 2.29, 'bow string course foot': 5.83,
                'bow upper transom bar': 4.85}   # inland-1888-bow-lights.json (T-2765), metres over grade
BOW_U_AT_11 = lf.CU + lf.R * math.cos(math.radians(11))   # the 11 degree light, which x 284-298 reads


def basis(yaw, roll, pitch):
    t, r, ph = map(math.radians, (yaw, roll, pitch))
    fwd = np.array([math.sin(t) * math.cos(ph), math.cos(t) * math.cos(ph), math.sin(ph)])
    right0 = np.array([math.cos(t), -math.sin(t), 0.0])
    up0 = np.cross(right0, fwd)
    return math.cos(r) * right0 + math.sin(r) * up0, -math.sin(r) * right0 + math.cos(r) * up0, fwd


def project(c, P):
    right, up, fwd = basis(c['yaw'], c['roll'], c['pitch'])
    d = np.asarray(P, float) - (c['u'], c['v'], c['y'])
    z = d @ fwd
    xn, yn = (d @ right) / z, (d @ up) / z
    s = 1 + c['k1'] * (xn * xn + yn * yn)
    return c['cx'] + c['f'] * xn * s, c['cy'] - c['f'] * yn * s


def in_plan(c, u, v):
    """A loggia plan point moved and scaled as the plan hypotheses say."""
    return (LOGGIA_CENTRE[0] + c['L'] * (u - LOGGIA_CENTRE[0]) + c['du'],
            LOGGIA_CENTRE[1] + c['L'] * (v - LOGGIA_CENTRE[1]) + c['dv'])


def bow_y(c, y):
    return y * c['kb']


def residuals(c):
    out = []
    for lab, deg, half, y, (xl, xr) in lf.JAMBS:
        xs = {r: (project(c, lf.on_bow(deg - half, r, bow_y(c, y)))[0],
                  project(c, lf.on_bow(deg + half, r, bow_y(c, y)))[0]) for r in (lf.R_SASH, lf.R)}
        a, b = xs[lf.R_SASH], xs[lf.R]
        out += [(lab + ' left jamb', max(min(a), min(b)) - xl), (lab + ' right jamb', min(max(a), max(b)) - xr)]
    for lab, deg, y, py in lf.HEADS:
        y = c['hh'] if ('principal' in lab and 'head' in lab) else y
        out.append((lab, project(c, lf.on_bow(deg, lf.R_SASH, bow_y(c, y)))[1] - py))
    for lab, P, (x, _) in lf.FRONT:
        out.append((lab, project(c, P)[0] - x))
    for lab, kind, pts, side, x in lf.SILHOUETTES:
        if kind == 'box':
            cu, cv = in_plan(c, np.mean([p[0] for p in pts]), np.mean([p[1] for p in pts]))
            xs = [project(c, [cu + su * 0.3 * c['w'], cv + sv * 0.45 * c['w'], 2.5])[0]
                  for su in (-1, 1) for sv in (-1, 1)]
        else:
            (u, v), = pts
            pc = PAIR_CENTRES[0] if v < LOGGIA_CENTRE[1] else PAIR_CENTRES[1]
            u, v = in_plan(c, u, pc + c['m'] * (v - pc))
            d = np.array([u - c['u'], v - c['v']])
            n = np.array([-d[1], d[0]]) / np.linalg.norm(d)
            r = lf.SHAFT_R * c['m']
            xs = [project(c, [u + s * r * n[0], v + s * r * n[1], lf.SHAFT_Y])[0] for s in (-1, 1)]
        out.append((lab, (min(xs) if side == 'left' else max(xs)) - x))
    for lab, P, y in lf.HEIGHTS:
        u, v = in_plan(c, P[0], P[1])
        out.append((lab, project(c, [u, v, c['D'] + c['k'] * (P[2] - lf.DECK)])[1] - y))
    return out


def fit(free):
    names = ['u', 'v', 'yaw', 'roll', 'f', 'cy'] + free
    lo, hi = [BOUNDS[n][0] for n in names], [BOUNDS[n][1] for n in names]
    best = None
    for yaw0 in (305, 317, 325):
        for d0 in (10, 16, 24):
            t = math.radians(yaw0)
            c0 = dict(DEFAULT, u=20.0 - d0 * math.sin(t), v=4.0 - d0 * math.cos(t), yaw=yaw0, roll=0.0,
                      f=34.0 * d0, cy=276.0)
            q0 = [min(max(c0[n], l + 1e-3), h - 1e-3) for n, l, h in zip(names, lo, hi)]

            def resid(q, c0=c0):
                c = dict(c0, **dict(zip(names, q)))
                return np.array([r for _, r in residuals(c)] + [c['roll'] / 1.5])
            s = least_squares(resid, q0, bounds=(lo, hi), x_scale='jac', max_nfev=20000)
            if best is None or s.cost < best[0].cost:
                best = (s, c0)
    s, c0 = best
    c = dict(c0, **dict(zip(names, s.x)))
    at_bound = [n for n, v, l, h in zip(names, s.x, lo, hi) if min(v - l, h - v) < 1e-2 * (h - l)]
    return c, residuals(c), at_bound


def nickel():
    """Nickel 1967's rows against its committed camera (T-1883's, on the front's corners only)."""
    cam = json.loads(NICKEL.read_text())
    right, up, fwd = (np.array(v, float) for v in cam['basis_right_up_forward'])
    eye = np.array(cam['eye'], float)

    def row(P):
        d = np.asarray(P, float) - eye
        return float(cam['principal_px'][1] - cam['focal_px'] * (d @ up) / (d @ fwd))
    drawn = {
        'south pair capital top': row([20.625, 7.45, 5.095]),
        'south pedestal cap arris': row([20.7, 7.45, 2.88]),
        'bow principal sill': row([BOW_U_AT_11, lf.CV + lf.R * math.sin(math.radians(11)), PLATE_LEVELS['bow principal sill']]),
        'bow string course foot': row([BOW_U_AT_11, lf.CV + lf.R * math.sin(math.radians(11)), PLATE_LEVELS['bow string course foot']]),
        'bow principal glass head': row([BOW_U_AT_11, lf.CV + lf.R * math.sin(math.radians(11)), 5.30]),
        'bow upper transom bar': row([BOW_U_AT_11, lf.CV + lf.R * math.sin(math.radians(11)), PLATE_LEVELS['bow upper transom bar']]),
    }
    rows = [{'edge': k, 'print_y': v, 'read': why, 'camera_y': round(drawn[k], 1),
             'dy_px': round(v - drawn[k], 1)} for k, (v, why) in NICKEL_READS.items()]
    span = lambda a, b, src: src[b] - src[a]
    pr = {k: v for k, (v, _) in NICKEL_READS.items()}
    col_p, col_c = span('south pair capital top', 'south pedestal cap arris', pr), \
        span('south pair capital top', 'south pedestal cap arris', drawn)
    bow_p, bow_c = span('bow string course foot', 'bow principal sill', pr), \
        span('bow string course foot', 'bow principal sill', drawn)
    return {
        'camera': str(NICKEL.relative_to(ROOT)), 'rows': rows,
        'column_px': {'print': col_p, 'camera': round(col_c, 1), 'ratio': round(col_p / col_c, 3)},
        'bow_sill_to_string_course_px': {'print': bow_p, 'camera': round(bow_c, 1), 'ratio': round(bow_p / bow_c, 3)},
        'column_over_bow_span': {'print': round(col_p / bow_p, 3), 'model': round(col_c / bow_c, 3),
                                 'factor': round((col_p / bow_p) / (col_c / bow_c), 3)},
        'glass_head_below_string_course_px': {'print': round(pr['bow principal glass head'] - pr['bow string course foot'], 1),
                                               'camera_at_5.30_m': round(drawn['bow principal glass head'] - drawn['bow string course foot'], 1),
                                               'camera_at_transom_bar_4.85_m': round(drawn['bow upper transom bar'] - drawn['bow string course foot'], 1)},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help=f'write {REPORT.relative_to(ROOT)}')
    args = ap.parse_args()
    sha = hashlib.sha256(lf.GLB.read_bytes()).hexdigest()
    made_on = json.loads(MATCH.read_text())['glb_sha256']
    if sha != made_on:
        raise SystemExit(f'{lf.GLB.name} is {sha[:12]}, not the {made_on[:12]} the match record was made on: '
                         'check the bow\'s openings and the loggia did not move, then re-render the view')
    table = []
    for group, label, free in HYPOTHESES:
        c, res, at_bound = fit(free)
        r = np.array([v for _, v in res])
        q = {'group': group, 'hypothesis': label, 'free': free, 'n': len(r),
             'rms_px': round(float(np.sqrt((r ** 2).mean())), 2), 'max_px': round(float(abs(r).max()), 2),
             'eye_uvy': [round(float(c[n]), 2) for n in ('u', 'v', 'y')], 'yaw_deg': round(float(c['yaw']), 2),
             'focal_px': round(float(c['f']), 1), 'principal_px': [round(float(c['cx']), 1), round(float(c['cy']), 1)],
             'params': {n: round(float(c[n]), 3) for n in free}, 'at_bound': at_bound,
             'loggia_heights_dy_px': {lab: round(float(v), 1) for lab, v in res[-len(lf.HEIGHTS):]}}
        table.append(q)
        print(f"{group:8s} {label:46s} RMS {q['rms_px']:5.2f} max {q['max_px']:5.1f} px  "
              + ' '.join(f'{n} {v}' for n, v in q['params'].items())
              + (f"  at bound: {', '.join(at_bound)}" if at_bound else ''))
    third = nickel()
    print('Nickel 1967:', ', '.join(f"{r['edge']} {r['print_y']} vs {r['camera_y']}" for r in third['rows']))
    print(f"  column over the bow's sill-to-string-course span: print {third['column_over_bow_span']['print']}, "
          f"model {third['column_over_bow_span']['model']}, factor {third['column_over_bow_span']['factor']}")
    if args.write:
        REPORT.write_text(json.dumps({
            '_doc': 'Written by tools/keith_1965_cause_fit.py (T-2830): T-2764\'s controls on the 1965 close view of '
                    'Keith\'s loggia fitted under one hypothesis at a time (optics, the bow, the loggia\'s plan, its '
                    'heights), and Nickel 1967 read beside it; read the tool\'s docstring for what is fitted.',
            'print': 'data/sources/assets/inland_architect_1888_02_keith/a18-gh-1808-porch-1965.jpg',
            'glb': str(lf.GLB.relative_to(ROOT)), 'glb_sha256': sha, 'points_read_on': lf.GLB_SHA256,
            'hypotheses': table, 'nickel_1967': third}, indent=1) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
