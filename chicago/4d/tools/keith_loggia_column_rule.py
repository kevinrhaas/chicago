#!/usr/bin/env python3
"""T-2831: Keith's loggia column ruled between the 1888 plate, Nickel 1967 and the 1965 slide.

T-2830 left the column standing between three pictures: the 1888 plate, on whose level fits T-2763
built it (2.2 m over a 0.88 m pedestal), and two late pictures that stood it about 1.3 times taller
against the bow (the 1965 slide's k 1.29 on a camera fitted to the bow's lights; Nickel 1967's 1.30
against the bow's sill-to-string-course span). Each late reading leans on the bow. This reads the
bow and the column in all three pictures with the same rulers, and asks which height the house is
built to.

  1. THE BOW'S PRINCIPAL HEADS, CAMERA-FREE. Down one light's own column the sill, the top of the
     glass and the string course's foot stand on one vertical at one depth, so in a level view their
     rows are linear in height: the head stands at sill + (sill - head) / (sill - string) of the
     sill-to-string span (2.35 to 5.83 m, T-2765's plate reading as built). The plate draws its
     principal lights in three tiers, the top light 4.85-5.30 m over a stone bar (T-2815). A late
     picture whose glass stops at the middle light's head (4.70 m) has blinded the top lights, and a
     camera that pairs that edge with the 5.30 m head is fitted to the wrong height.

  2. THE COLUMN AGAINST THE BOW'S SPAN, both near-square views from across Prairie Avenue (the
     plate's eye at u 39.2 and Nickel's at u 38.4): the column's print length over the sill-to-
     string span, against the same ratio its committed camera draws for the model, so the loggia's
     nearer depth is the camera's and the ratio's scale is the print's own. Nickel's capital top is
     RE-READ (NICKEL_CAPITAL): T-2830's y 623.5 is where the cornice's shadow ends, the top of the
     beam; the beam's lit face runs 624-639 and the shadow under it lies at 640-643, which is where
     the camera draws the capital's top (642.4) and the record's stack puts it (STACK, printed beside
     the luminance column).

  3. THE 1965 SLIDE RE-FITTED with its heads paired where it shows them. T-2830's fits
     (tools/keith_1965_cause_fit.py, T-2764's 29 coordinates unchanged) are run again with the three
     principal heads at the middle light's head (4.70 m) instead of 5.30 m, and the loggia given a
     factor k on its heights, a move in plan, or both.

  python3 tools/keith_loggia_column_rule.py            # print the reading
  python3 tools/keith_loggia_column_rule.py --write    # and write REPORT

What it does not do: move the model, re-solve any committed camera, or rule the loggia's place in
plan (which part 3 reports and leaves to its own ticket).
"""
from pathlib import Path
import argparse, hashlib, json, math, sys
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import keith_1965_level_fit as lf  # noqa: E402  T-2764's bow geometry and controls
import keith_1965_cause_fit as cf  # noqa: E402  T-2830's fitter

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / 'data/reference_views/keith_house_1808_prairie'
ASSETS = ROOT / 'data/sources/assets/inland_architect_1888_02_keith'
REPORT = ROOT / 'docs/RESEARCH/photo-match/keith_house_1808_prairie/keith-loggia-column-rule.json'
SILL, STRING = 2.35, 5.83          # the principal sill and the string course's foot, as built (T-2765)
TIERS = {'middle light head': 4.70, 'upper bar top': 4.85, 'top light head': 5.30}   # T-2815's tiers
CAPITAL_TOP, CAP_ARRIS = 5.095, 2.88   # the abacus's front edge and the pedestal cap's arris (T-2763)
PAIR_V = {'south': 7.45, 'north': 9.95}

# Each picture's rows down one principal light's column: sill (the glass's foot), the top of the glass,
# the string course's foot; and the loggia's capital tops and pedestal cap arrises.
PICTURES = {
    'inland-1888': {
        'print': 'plate.jpg', 'camera': 'inland-1888.json', 'bearing': -33,
        'bow': {'sill': 1617.0, 'glass head': 1382.0, 'string foot': 1342.0},
        'bow_read': 'tools/keith_bow_lights_read.py (T-2765), the south light\'s column x 405-485',
        'loggia': {'south': (1383.5, 1575.0), 'north': (1392.0, 1577.0)},
        'loggia_read': 'tools/keith_plate_level_fit.py (T-2749/T-2763) controls',
    },
    'nickel-1967': {
        'print': 'nickel-1967.jpg', 'camera': 'nickel-1967.json', 'bearing': 11,
        'bow': {'sill': 701.5, 'glass head': 647.5, 'string foot': 620.0},
        'bow_read': 'tools/keith_1965_cause_fit.py NICKEL_READS (T-2830), x 284-298 and 274-279',
        'loggia': {'south': (639.5, 696.5)},
        'loggia_read': 'capital top re-read here (NICKEL_CAPITAL); pedestal cap T-2830\'s',
    },
    'a18-gh-1808-porch-1965': {
        'print': 'a18-gh-1808-porch-1965.jpg', 'camera': 'a18-gh-1808-porch-1965.json', 'bearing': -33,
        'bow': {'sill': 244.5, 'glass head': 134.0, 'string foot': 78.0},
        'bow_read': 'tools/keith_1965_level_fit.py HEADS (T-2764), and T-2764\'s string course foot (y 78)',
        'loggia': {'south': (134.5, 235.5), 'north': (152.5, 241.0)},
        'loggia_read': 'tools/keith_1965_level_fit.py HEIGHTS (T-2764)',
    },
}
# Nickel's south pair, luminance down x 339-346 (mean, 1 px steps): the cornice's shadow 618-623, the
# beam's lit face 624-639, the shadow under the beam 640-643 (darkest 642), the shafts lit 645-688,
# the shadow over the pedestal's cap 690-699 (darkest 697-698), the pedestal's face lit from 701.
NICKEL_CAPITAL = {'edge': 639.5, 'darkest': 642.0, 'x': (339, 347), 'rows': (596, 706)}
# The record's stack over Nickel's south pair (the record's loggia: pedestal 0.88, column 2.2,
# entablature 0.9, balcony 0.75 on a 2.0 m deck), drawn on Nickel's camera beside the profile.
STACK = {'balcony top': 6.73, 'beam top (cornice)': 5.98, 'capital top': CAPITAL_TOP, 'pedestal cap': CAP_ARRIS}
REFITS = [  # (label, principal heads at, free parameters beyond the level camera's six)
    ('T-2830: heads at 5.30, k', 5.30, ['k']),
    ('heads at 4.70', 4.70, []),
    ('heads at 4.70, k', 4.70, ['k']),
    ('heads at 4.70, loggia moved south/north (dv)', 4.70, ['dv']),
    ('heads at 4.70, dv and k', 4.70, ['dv', 'k']),
    ('heads at 4.70, du, dv and k', 4.70, ['du', 'dv', 'k']),
    ('heads at 5.30, dv', 5.30, ['dv']),
]


def camera(name):
    """A committed camera as (eye, right, up, forward, focal, principal)."""
    cam = json.loads((VIEWS / name).read_text())
    if 'basis_right_up_forward' in cam:
        right, up, fwd = (np.array(v, float) for v in cam['basis_right_up_forward'])
    else:  # a level camera stored by heading alone (T-2763's plate camera)
        t = math.radians(cam['yaw_deg'])
        fwd, right, up = np.array([math.sin(t), math.cos(t), 0.0]), np.array([math.cos(t), -math.sin(t), 0.0]), \
            np.array([0.0, 0.0, 1.0])
    return np.array(cam['eye'], float), right, up, fwd, float(cam['focal_px']), cam['principal_px']


def row(cam, P):
    eye, right, up, fwd, f, pp = cam
    d = np.asarray(P, float) - eye
    return float(pp[1] - f * (d @ up) / (d @ fwd))


def read_picture(key, p):
    cam = camera(p['camera'])
    b = p['bow']
    frac = (b['sill'] - b['glass head']) / (b['sill'] - b['string foot'])
    head_m = SILL + frac * (STRING - SILL)
    on = lambda r, y: lf.on_bow(p['bearing'], r, y)
    span_c = row(cam, on(lf.R_SASH, SILL)) - row(cam, on(lf.R, STRING))
    span_p = b['sill'] - b['string foot']
    pairs = {}
    for pair, (top, cap) in p['loggia'].items():
        v = PAIR_V[pair]
        col_c = row(cam, [20.7, v, CAP_ARRIS]) - row(cam, [20.625, v, CAPITAL_TOP])
        col_p = cap - top
        pairs[pair] = {'column_px': {'print': col_p, 'camera': round(col_c, 1)},
                       'column_over_bow_span': {'print': round(col_p / span_p, 3), 'model': round(col_c / span_c, 3),
                                                'factor': round((col_p / span_p) / (col_c / span_c), 3)},
                       'column_m_on_the_span': round(2.2 * (col_p / span_p) / (col_c / span_c), 2)}
    return {'print': f'data/sources/assets/inland_architect_1888_02_keith/{p["print"]}',
            'camera': f'data/reference_views/keith_house_1808_prairie/{p["camera"]}',
            'bow_rows': b, 'bow_read': p['bow_read'], 'loggia_read': p['loggia_read'],
            'glass_head_fraction_of_span': round(frac, 4), 'glass_head_m': round(head_m, 2),
            'glass_head_is': min(TIERS, key=lambda k: abs(TIERS[k] - head_m)),
            'bow_span_px': {'print': span_p, 'camera': round(span_c, 1)}, 'pairs': pairs}


def nickel_profile():
    a = np.asarray(Image.open(ASSETS / 'nickel-1967.jpg').convert('L'), float)
    x0, x1 = NICKEL_CAPITAL['x']
    lum = {y: round(float(a[y, x0:x1].mean())) for y in range(*NICKEL_CAPITAL['rows'])}
    cam = camera('nickel-1967.json')
    drawn = {k: round(row(cam, [20.625 if k != 'pedestal cap' else 20.7, PAIR_V['south'], z]), 1)
             for k, z in STACK.items()}
    return lum, drawn


def refits():
    out = []
    for label, hh, free in REFITS:
        cf.DEFAULT['hh'] = hh
        c, res, at_bound = cf.fit(free)
        r = np.array([v for _, v in res])
        d = dict(res)
        out.append({'fit': label, 'heads_m': hh, 'free': free, 'rms_px': round(float(np.sqrt((r ** 2).mean())), 2),
                    'max_px': round(float(abs(r).max()), 2), 'params': {n: round(float(c[n]), 3) for n in free},
                    'eye_uv': [round(float(c['u']), 2), round(float(c['v']), 2)], 'at_bound': at_bound,
                    'principal_heads_dy_px': {k: round(float(v), 1) for k, v in d.items() if 'principal' in k
                                              and ('head' in k or 'sill' in k)},
                    'loggia_heights_dy_px': {lab: round(float(d[lab]), 1) for lab, _, _ in lf.HEIGHTS}})
    cf.DEFAULT['hh'] = 5.30
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help=f'write {REPORT.relative_to(ROOT)}')
    args = ap.parse_args()
    sha = hashlib.sha256(lf.GLB.read_bytes()).hexdigest()
    made_on = json.loads(cf.MATCH.read_text())['glb_sha256']
    if sha != made_on:
        raise SystemExit(f'{lf.GLB.name} is {sha[:12]}, not the {made_on[:12]} the 1965 record was made on: '
                         'check the bow\'s openings and the loggia did not move, then re-read')
    pictures = {k: read_picture(k, p) for k, p in PICTURES.items()}
    for k, q in pictures.items():
        print(f"{k:24s} glass head at {q['glass_head_fraction_of_span']:.3f} of the sill-to-string span: "
              f"{q['glass_head_m']:.2f} m ({q['glass_head_is']})")
        for pair, v in q['pairs'].items():
            c = v['column_over_bow_span']
            print(f"{'':24s} {pair} column over the bow's span: print {c['print']}, model {c['model']}, "
                  f"factor {c['factor']} (a {v['column_m_on_the_span']} m column)")
    lum, drawn = nickel_profile()
    print('Nickel 1967, x 339-346:', ' '.join(f'{y}:{v}' for y, v in lum.items() if 612 <= y <= 704))
    print('  the record\'s stack drawn on its camera:', ', '.join(f'{k} {v}' for k, v in drawn.items()))
    table = refits()
    for q in table:
        print(f"1965 {q['fit']:44s} RMS {q['rms_px']:5.2f} max {q['max_px']:5.1f}  {q['params']}  "
              f"loggia {list(q['loggia_heights_dy_px'].values())}")
    if args.write:
        REPORT.write_text(json.dumps({
            '_doc': 'Written by tools/keith_loggia_column_rule.py (T-2831): the bow\'s principal heads read camera-free '
                    'in the 1888 plate, Nickel 1967 and the 1965 slide; the loggia\'s column against the bow\'s '
                    'sill-to-string-course span on each committed camera, Nickel\'s capital top re-read; the 1965 '
                    'slide re-fitted with its heads at the middle light\'s head. Read the tool\'s docstring.',
            'glb': str(lf.GLB.relative_to(ROOT)), 'glb_sha256': sha, 'built': {
                'column_m': 2.2, 'pedestal_m': 0.88, 'capital_top_m': CAPITAL_TOP, 'pedestal_cap_m': CAP_ARRIS,
                'principal_sill_m': SILL, 'string_course_foot_m': STRING, 'tiers_m': TIERS},
            'pictures': pictures,
            'nickel_capital_reread': {**NICKEL_CAPITAL, 'luminance': lum, 'stack_drawn_on_camera': drawn,
                                      'stack_m': STACK, 't2830_read': 623.5},
            'refits_1965': table}, indent=1) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
