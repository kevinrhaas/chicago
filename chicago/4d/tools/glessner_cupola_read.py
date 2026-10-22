#!/usr/bin/env python3
"""T-3031: how tall, how wide and where on the ridge is Glessner's stable cupola?

T-3030 left the two northwest prints disagreeing about the cupola: read through the
committed Cornell camera (a west-wall homography on two reconstructed eaves) its eave
and apex stood about 27-32 px higher against the gable than HABS photograph 1 put
them, and photograph 1's cupola looked about 25 px narrower than the build. Neither
committed camera was fitted at the stable, so neither print could say which.

This tool reads the cupola through the cameras T-2758 re-solved on MEASURED controls
at the stable (the carriage doorway, sheet 2's jambs and sheet 5's 12.6 ft soffit;
in the Cornell view both stable faces' corners and the loft opening's jambs), then
takes out each camera's remaining local offset at the stable end by holding the
north gable's coping apex where each print draws it (a translation, so each print
reads the cupola AGAINST THE ROOF it stands on, which is the question). Through
those two cameras it fits the cupola's own numbers -- body half-width, eave overhang,
eave height, apex height and centre S on the W 141 ridge -- to hand picks of the
pyramid's apex, its eave corners and the body's corner arrises in both prints at
once. Photograph 1 alone cannot place the cupola on S (every control lies in the
north face, T-2758); the Cornell view sees two faces and can.

    python3 tools/glessner_cupola_read.py            # print the fit
    python3 tools/glessner_cupola_read.py --write    # and write the report
    python3 tools/glessner_cupola_read.py --check    # re-derive; fail on drift

The report is data/comparisons/glessner/stable-cupola.json. A dated reading that
the cupola record cites, not a per-commit gate.
"""
from pathlib import Path
import argparse, json, sys
import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, str(Path(__file__).resolve().parent))
import glessner_stable_roof_read as roof  # noqa: E402  (T-2758's cameras and projection)

ROOT = roof.ROOT
REPORT = ROOT / 'data/comparisons/glessner/stable-cupola.json'
STRUCTURE = ROOT / 'data/structures/glessner_house.json'

# The T-2758 fits each print is read through: the lowest-RMS camera each photograph's
# measured controls give (photograph 1 with its eye height free, 3.09 px; the Cornell
# view pitched, 3.65 px).
CAMERAS = {'habs01': 'doorway_eye_height', 'cornell': 'roof_pitched'}
# The local anchor: the north gable's coping apex, where its two slopes meet (T-2758's
# own picks), on the W 141 ridge axis in the S 0 face.
ANCHOR = {'habs01': (1240, 357), 'cornell': (711, 217)}

# Hand picks in each print's own committed pixels, read at 5-8x with the contrast
# stretched. Corners are named by plan quarter (NE = low W, low S). The pyramid is
# read where its hips meet, under the finial knob (photograph 1) and the cap
# (Cornell, whose cap hides the point: +/-4 px there). The Cornell view's NE eave
# tip and the body's NE arris are behind the pole's crossarm and are not picked.
PICKS = {
    'habs01': [
        ('apex', None, (1312.0, 303.0)),
        ('eave', 'NE', (1259.7, 365.8)),   # the left silhouette's eave tip
        ('eave', 'NW', (1340.0, 357.0)),   # the near corner, where the lit face's eave kinks
        ('eave', 'SW', (1369.2, 386.7)),   # the right silhouette's flared tip
        ('body', 'NE', (1277.5, 378.0)),   # the body's left arris under the eave
        ('body', 'NW', (1338.0, 385.0)),   # its near arris
        ('body', 'SW', (1360.0, 390.0)),   # its right arris
    ],
    'cornell': [
        ('apex', None, (916.0, 124.0)),
        ('eave', 'NW', (927.0, 211.6)),    # the near corner: the north face's eave meets the west face's
        ('eave', 'SW', (1019.0, 261.0)),   # the west face's flared tip
        ('body', 'NW', (927.4, 240.0)),    # the near arris, straight under the eave's corner
        ('body', 'SW', (1002.0, 270.0)),   # the right arris
    ],
}
SIGN = {'NE': (-1, -1), 'NW': (1, -1), 'SW': (1, 1), 'SE': (-1, 1)}   # (W, S) signs
RIDGE_W = 141.0
# The cupola as T-3030 left it, the fit's fixed starting point and the baseline the
# ruled record is measured against.
BEFORE = {'half_ft': 3.0, 'overhang_ft': 1.25, 'eave_ft': 40.9, 'apex_ft': 47.0, 'centre_S': 14.6}


def record():
    return json.loads(STRUCTURE.read_text())['phases'][0]['form']['turret_stable']['value']


def built(t):
    """The build's own numbers in this tool's parameters."""
    return {'half_ft': t['plan_ft'] / 2, 'overhang_ft': t['eave']['overhang_ft'],
            'eave_ft': round(t['body_top'][0] - t['eave']['drop_ft'], 3), 'apex_ft': t['apex'][0],
            'centre_S': t['centre_S']}


def cameras():
    model = roof.model_heights()
    h, _ = roof.habs01(model)
    c = roof.cornell(model)
    out = {}
    for photo, recs in (('habs01', h), ('cornell', c)):
        r = recs[CAMERAS[photo]]['camera']
        cam = roof.Cam(r['eye'], r['basis_right_up_forward'], r['focal_px'], tuple(r['principal_px']), r['pixel_aspect'])
        apex = cam.project(roof.world(RIDGE_W, 0, model['gable_coping_apex_ft']))
        out[photo] = (cam, np.array(ANCHOR[photo]) - apex)
    return out, model


def project(cam, shift, W, S, z):
    return cam.project(roof.world(W, S, z)) + shift


def residuals(p, cams, photos):
    half, ov, ze, apex, cS = p
    out = []
    for photo in photos:
        cam, shift = cams[photo]
        for kind, corner, (u, v) in PICKS[photo]:
            if kind == 'apex':
                q = project(cam, shift, RIDGE_W, cS, apex)
                out += [q[0] - u, q[1] - v]
            elif kind == 'eave':
                sw, ss = SIGN[corner]
                q = project(cam, shift, RIDGE_W + sw * (half + ov), cS + ss * (half + ov), ze)
                out += [q[0] - u, q[1] - v]
            else:   # a body arris: only its u is read, at the pick's height
                sw, ss = SIGN[corner]
                W, S = RIDGE_W + sw * half, cS + ss * half
                lo, hi = 20., 60.
                for _ in range(50):
                    mid = (lo + hi) / 2
                    if project(cam, shift, W, S, mid)[1] > v:
                        lo = mid
                    else:
                        hi = mid
                out.append(project(cam, shift, W, S, lo)[0] - u)
    return np.array(out)


def fit(cams, photos, start, fixed_S=None):
    if fixed_S is None:
        f = lambda x: residuals(x, cams, photos)
        x0 = start
    else:
        f = lambda x: residuals([*x, fixed_S], cams, photos)
        x0 = start[:4]
    s = least_squares(f, x0, x_scale='jac')
    x = list(s.x) + ([] if fixed_S is None else [fixed_S])
    r = f(s.x)
    # One-sigma from the Jacobian at the solution, scaled by the residual RMS.
    J = s.jac
    dof = max(len(r) - len(s.x), 1)
    sigma2 = float(r @ r) / dof
    try:
        cov = np.linalg.inv(J.T @ J) * sigma2
        sd = list(np.sqrt(np.diag(cov))) + ([] if fixed_S is None else [0.0])
    except np.linalg.LinAlgError:
        sd = [float('nan')] * 5
    names = ('half_ft', 'overhang_ft', 'eave_ft', 'apex_ft', 'centre_S')
    return {'params': {n: round(float(v), 2) for n, v in zip(names, x)},
            'one_sigma': {n: round(float(v), 2) for n, v in zip(names, sd)},
            'rms_px': round(float(np.sqrt(np.mean(r ** 2))), 2), 'max_px': round(float(np.abs(r).max()), 1),
            'residuals_px': [round(float(v), 1) for v in r]}


def derive():
    t = record()
    cams, model = cameras()
    order = ('half_ft', 'overhang_ft', 'eave_ft', 'apex_ft', 'centre_S')
    start = [BEFORE[k] for k in order]

    def by_photo(params):
        x = [params[k] for k in order]
        return {photo: {'rms_px': round(float(np.sqrt(np.mean(residuals(x, cams, [photo]) ** 2))), 2),
                        'residuals_px': [round(float(v), 1) for v in residuals(x, cams, [photo])]}
                for photo in PICKS}
    b = built(t)
    joint = fit(cams, ['habs01', 'cornell'], start)
    S = joint['params']['centre_S']
    return {
        'ticket': 'T-3031',
        'not_a_reading': 'A bounded re-reading of two catalogued photographs through T-2758\'s re-solved cameras; it rules the cupola record, it adds no source.',
        'sources': {'habs01': 'habs_glessner_photo_01_nw_1963', 'cornell': 'cornell_adw_glessner_stable_1887'},
        'cameras': {photo: {'t2758_fit': CAMERAS[photo], 'anchor_px': ANCHOR[photo],
                            'local_shift_px': [round(float(v), 1) for v in cams[photo][1]]} for photo in PICKS},
        'model_roof': {'gable_coping_apex_ft': model['gable_coping_apex_ft'], 'ridge_ft': model['ridge_ft'], 'ridge_W': model['ridge_W']},
        'picks': PICKS,
        'before_t3031': {'params': BEFORE, 'by_photo': by_photo(BEFORE)},
        'as_built': {'params': b, 'by_photo': by_photo(b)},
        'joint': joint,
        'habs01_alone_at_joint_S': fit(cams, ['habs01'], start, fixed_S=S),
        'cornell_alone': fit(cams, ['cornell'], start),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--write', action='store_true')
    g.add_argument('--check', action='store_true')
    a = ap.parse_args()
    report = json.loads(json.dumps(derive()))
    for key in ('before_t3031', 'as_built'):
        print(f"{key:<11}", json.dumps(report[key]['params']), {k: v['rms_px'] for k, v in report[key]['by_photo'].items()})
    for key in ('joint', 'habs01_alone_at_joint_S', 'cornell_alone'):
        v = report[key]
        print(f"{key:<11}", json.dumps(v['params']), '+/-', json.dumps(v['one_sigma']), f"rms {v['rms_px']} px (max {v['max_px']})")
    if a.write:
        REPORT.write_text(json.dumps(report, indent=1) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')
    elif a.check:
        if not roof.close(json.loads(REPORT.read_text()), report):
            sys.exit(f'{REPORT.relative_to(ROOT)} is stale: re-run with --write and review the change')
        print('stable-cupola reading re-derived: matches the committed report')


if __name__ == '__main__':
    main()
