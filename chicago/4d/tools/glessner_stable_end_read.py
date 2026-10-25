#!/usr/bin/env python3
"""T-3139: Glessner's stable end on HABS photographs 15 and 1, each through a camera
fitted at the stable.

HABS photograph 15 (`habs-15-stable-detail`) carried T-2200's frozen pinhole camera,
imported unchanged by T-2228 and never refitted: about 1.2 degrees of roll, 13-20 px
off at the loft, and so the hoist stone drawn about 15 px west of the print's (T-2849,
T-3136). Photograph 1's committed camera (`habs-01-northwest`) is a whole-house camera
fitted at the Prairie corner, about 28 px off at the stable 141 ft away (T-2758).

This tool re-solves HABS 15 on MEASURED controls in the stable's north face (S 0):
the carriage doorway (sheet 2's jambs W 134.9-147.0, sheet 5's 12.6 ft soffit, the
threshold at grade), the loft opening's and the flanking lights' jambs (sheet 3: W
137.5-144.7, 132.4-133.6, 149.1-150.3) and the face's north-west arris (W 161.25).
The fit is level (the print's verticals stand within 2 px over 150-340 px), at T-2200's
focal length and principal point: every control lies in the one face, seen square, so
the face fixes scale, level and the eye's height but cannot measure the lens's focal
length or its lateral shift (freed, the shift's one sigma is 253 px). The hoist's foot
lies in the face and is read here; its nose stands 4 ft off it, and its parallax rides
on exactly what the face cannot measure, so the nose is read in photograph 1 too.
Photograph 1 is read through T-2758's doorway re-solve with its eye height free (the
lowest-RMS fit of that print's own committed controls plus the same doorway,
tools/glessner_stable_roof_read.py), which keeps the Prairie corner and adds the
stable.

Through both it reads the stable end back as checks it was never fitted to: the
hoist stone (its foot at the wall and the nose's top and foot, the record's
`north_stable_fabric.hoist_stone`), the gable's two feet (`stable_north_gable`) and,
in HABS 15, the eave at the north-west corner. It never fits a building point.

    python3 tools/glessner_stable_end_read.py            # print the table
    python3 tools/glessner_stable_end_read.py --write    # and write the report
    python3 tools/glessner_stable_end_read.py --camera   # write HABS 15's refitted camera
    python3 tools/glessner_stable_end_read.py --check    # re-derive; fail on drift

The report is data/comparisons/glessner/stable-end.json. A dated reading, not a
per-commit gate.
"""
from pathlib import Path
import argparse, json, math, sys
import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, str(Path(__file__).resolve().parent))
import glessner_stable_roof_read as roof  # noqa: E402  (T-2758's cameras and projection)
from glessner_stable_roof_read import Cam, world, axes, residuals  # noqa: E402

ROOT = roof.ROOT
VIEWS = roof.VIEWS
REPORT = ROOT / 'data/comparisons/glessner/stable-end.json'
H15 = VIEWS / 'habs-15-stable-detail.json'

# T-2200's frozen pinhole, as HABS 15 carried it until this tool's --camera replaced it.
# Pinned here, never read off H15: --camera rewrites H15 with the stable_level fit, so a
# 'committed' row read from it would report the refit under T-2200's name, and every fit
# would start from its own output.
T2200 = {'eye': [14.79591352, 47.53954371, 2.5],
         'basis_right_up_forward': [[-0.9862459817, 0.1636606029, 0.0231099687],
                                    [0.0202996664, -0.0188233869, 0.9996167284],
                                    [-0.1640328843, -0.9863371063, -0.0152422341]],
         'focal_px': 1598.11111111, 'principal_px': [900, 603]}

# Hand picks in HABS 15's committed 1800 x 1275 pixels, read at 3-5x with the contrast
# stretched (about +/-2 px; the soffit is the lintel's shadow line, the threshold the
# sidewalk's bright edge between the cars, which hide the east jamb's foot).
H15_CONTROLS = [
    ('uv', (134.9, 0, 12.6), (1058.0, 485.5)),    # doorway east jamb at the soffit
    ('uv', (147.0, 0, 12.6), (1270.5, 485.5)),    # doorway west jamb at the soffit
    ('uv', (147.0, 0, 0.0), (1272.0, 703.0)),     # west jamb at the threshold
    ('soffit', (None, 0, 0.0), (1200.0, 703.5)),  # the threshold between the cars
    ('edge', (134.9, 0, None), (1056.5, 640.0)),  # east jamb low down
    ('edge', (137.5, 0, None), (1101.7, 340.0)),  # loft opening's jambs (sheet 3)
    ('edge', (144.7, 0, None), (1224.3, 340.0)),
    ('edge', (132.4, 0, None), (1005.0, 320.0)),  # the flanking lights' jambs (sheet 3)
    ('edge', (133.6, 0, None), (1028.3, 320.0)),
    ('edge', (149.1, 0, None), (1300.0, 320.0)),
    ('edge', (150.3, 0, None), (1321.7, 320.0)),
    ('edge', (161.25, 0, None), (1529.0, 300.0)),  # the north-west arris, high
    ('edge', (161.25, 0, None), (1530.0, 640.0)),  # and low
]
# The checks, never fitted: (name, plane, picked px). The hoist stone's lit underside
# runs from its foot at the wall up to the nose's end face (about 13 px wide); the
# gable's feet are where each coping slope ends on its kneeler.
H15_HOIST = {'foot': (1162.0, 253.0), 'nose_top': (1178.0, 209.6), 'nose_foot': (1178.0, 224.0)}
# Photograph 1 (1800 x 1289): from the north-west the nose stands clear of the wall,
# east of its own foot, and its lit end face is read at 7x between u 1218 and 1225 with
# its top at v 491 (the foot at the wall is lost in the stone's own cast shadow).
H01_HOIST = {'nose_top': (1221.5, 491.0)}


def model():
    form = json.loads((ROOT / 'data/structures/glessner_house.json').read_text())['phases'][0]['form']
    detail = None
    for v in form.values():
        if isinstance(v, dict) and isinstance(v.get('value'), dict) and 'north_stable_fabric' in v['value']:
            detail = v['value']
    hoist = detail['north_stable_fabric']['hoist_stone']
    mid = sum(hoist['W']) / 2
    lo, hi = hoist['z']
    under = hi - hoist['nose_ft']
    return {
        'hoist': {'W': hoist['W'], 'z': hoist['z'], 'projection_ft': hoist['projection_ft'], 'nose_ft': hoist['nose_ft'],
                  'points': {'foot': (mid, 0.0, lo), 'nose_top': (mid, -hoist['projection_ft'], hi),
                             'nose_foot': (mid, -hoist['projection_ft'], under)}},
    }


def h15_cameras():
    d = T2200
    committed = Cam.committed(d)
    c = tuple(d['principal_px'])
    e = d['eye']
    fw = np.array(d['basis_right_up_forward'][2])
    yaw0 = math.atan2(fw[0], fw[1])
    f0 = d['focal_px']
    return committed, {
        'committed': ('T-2200\'s frozen pinhole, unchanged', None, None),
        'stable_level': ('level (the print\'s verticals do not lean: the NW arris and the east jamb stand within 2 px over 150-340 px), '
                         'focal and principal point held; eye position and heading free',
                         lambda x: Cam(x[:3], axes(x[3], 0., 0.), f0, c), [e[0], e[1], e[2], yaw0]),
        'stable_level_roll': ('as stable_level, roll free',
                              lambda x: Cam(x[:3], axes(x[3], 0., x[4]), f0, c), [e[0], e[1], e[2], yaw0, 0.]),
        'stable_level_shift': ('as stable_level, the lens\'s lateral shift (principal x) free: the face cannot measure it',
                               lambda x: Cam(x[:3], axes(x[3], 0., 0.), f0, (x[4], c[1])), [e[0], e[1], e[2], yaw0, c[0]]),
    }


def read(cam, picks, points):
    out = {}
    for name, px in picks.items():
        p = cam.project(world(*points[name]))
        out[name] = {'model_px': [round(float(p[0]), 1), round(float(p[1]), 1)], 'print_px': list(px),
                     'du_dv_px': [round(float(p[0] - px[0]), 1), round(float(p[1] - px[1]), 1)]}
    return out


def summarise(cam, obs, m, hoist_picks):
    r = residuals(cam, obs)
    f = cam.B[2]
    roll = math.degrees(math.atan2(cam.B[0][2], cam.B[1][2]))
    return {'fitted_obs': int(len(r)), 'rms_px': round(float(np.sqrt(np.mean(r ** 2))), 2),
            'max_px': round(float(np.abs(r).max()), 1),
            'roll_deg': round(roll, 2), 'pitch_deg': round(math.degrees(math.asin(f[2])), 2),
            'px_per_ft_at_doorway': round(float(cam.px_per_ft(141, 0, 6.3)), 2),
            'hoist': read(cam, hoist_picks, m['hoist']['points']),
            'camera': cam.record()}


def derive():
    m = model()
    committed, variants = h15_cameras()
    h15 = {}
    for key, (why, build, x0) in variants.items():
        if build is None:
            h15[key] = {'what': why, **summarise(committed, H15_CONTROLS, m, H15_HOIST)}
            continue
        s = least_squares(lambda x: residuals(build(x), H15_CONTROLS), x0, x_scale='jac')
        cam = build(s.x)
        h15[key] = {'what': why, **summarise(cam, H15_CONTROLS, m, H15_HOIST)}
        r = residuals(cam, H15_CONTROLS)
        sd = np.sqrt(np.diag(np.linalg.pinv(s.jac.T @ s.jac) * np.mean(r ** 2)))
        h15[key]['eye_W_S_height_ft'] = [round(161.25 - cam.eye[0] / roof.FT, 1), round(74 - cam.eye[1] / roof.FT, 1), round(cam.eye[2] / roof.FT, 2)]
        h15[key]['one_sigma_eye_m'] = [round(float(v), 2) for v in sd[:3]]
        if key == 'stable_level_shift':
            h15[key]['one_sigma_principal_x_px'] = round(float(sd[4]), 0)
    h01 = {}
    rm = roof.model_heights()
    fits, _ = roof.habs01(rm)
    door = [('uv', w, p) for w, p in roof.HABS01_DOOR]
    for key in ('committed', 'doorway_eye_height'):
        c = fits[key]['camera']
        cam = Cam(c['eye'], c['basis_right_up_forward'], c['focal_px'], tuple(c['principal_px']), c['pixel_aspect'])
        h01[key] = {'what': fits[key]['what'], 'rms_px_all_controls': fits[key]['rms_px'],
                    **summarise(cam, door, m, H01_HOIST)}
        h01[key]['note'] = 'fitted_obs / rms_px / max_px are over the doorway alone'
    return {
        'ticket': 'T-3139',
        'not_a_reading': 'A bounded re-reading of two catalogued photographs through cameras refitted on measured controls at the stable; no building point is fitted.',
        'sources': {'habs15': 'habs_glessner_photo_15_north_stable_1965', 'habs01': 'habs_glessner_photo_01_nw_1963',
                    'controls': 'habs_glessner_house_il_1015_drawings (sheet 2 doorway jambs W 134.9-147.0; sheet 3 loft and light jambs; sheet 5 soffit 12.6 ft)'},
        'model': m,
        'picks': {'habs15_controls': H15_CONTROLS, 'habs15_hoist': H15_HOIST, 'habs01_hoist': H01_HOIST},
        'habs15': h15, 'habs01': h01,
    }


def camera_file(report):
    d = json.loads(H15.read_text())
    fit_ = report['habs15']['stable_level']
    cam = fit_['camera']
    d['eye'] = cam['eye']
    d['basis_right_up_forward'] = cam['basis_right_up_forward']
    d['focal_px'] = cam['focal_px']
    d['principal_px'] = cam['principal_px']
    hz = fit_['hoist']
    d['solve'].update({
        'method': ('T-3147 (piece of T-3139) refits T-2200\'s frozen pinhole at the stable (tools/glessner_stable_end_read.py): '
                   'level, at T-2200\'s focal length and principal point, with the eye\'s position and the heading free, on measured '
                   'controls in the north face S 0 -- sheet 2\'s doorway jambs W 134.9-147.0, sheet 5\'s 12.6 ft soffit and the '
                   'threshold, sheet 3\'s loft (W 137.5-144.7) and flanking-light jambs (132.4-133.6, 149.1-150.3), and the north-west '
                   'arris W 161.25. The print\'s verticals stand within 2 px, so it is level; roll freed takes the RMS to 2.5 px at -0.9 '
                   'degrees by leaning the arris against its own picks.'),
        'record': 'data/comparisons/glessner/stable-end.json#habs15.stable_level',
        'fit_controls': fit_['fitted_obs'],
        'fit_rms_px': fit_['rms_px'],
        'withheld_checks': len(H15_HOIST),
        'roll_deg': fit_['roll_deg'],
        'hoist_check_px': {k: v['du_dv_px'] for k, v in hz.items()},
    })
    for k in ('baseline_fit_rms_px', 'baseline_check_rms_px'):
        d['solve'].pop(k, None)
    d['solve']['limitations'] = ('1965 plate; parked cars hide grade at the east jamb and the film holder hides the gable apex and cupola. '
                                 'Every control lies in the one north-face plane, seen square, so the focal length (held at T-2200\'s) and the '
                                 'lens\'s lateral shift (held at its principal point; freed, one sigma 253 px) are not measured: anything '
                                 'standing off the face, the hoist stone\'s nose included, is placed by them. Hand picks about +/-2 px.')
    d['solve']['warning'] = 'Lighting: see light (T-2848).'
    return json.dumps(d, indent=2) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--write', action='store_true')
    g.add_argument('--camera', action='store_true')
    g.add_argument('--check', action='store_true')
    a = ap.parse_args()
    report = json.loads(json.dumps(derive()))
    for photo in ('habs15', 'habs01'):
        for key, v in report[photo].items():
            print(f"{photo}.{key}: rms {v['rms_px']} px (max {v['max_px']}) over {v['fitted_obs']}; roll {v['roll_deg']} deg; "
                  f"{v['px_per_ft_at_doorway']} px/ft")
            print('    hoist', {k: x['du_dv_px'] for k, x in v['hoist'].items()})
    if a.write:
        REPORT.write_text(json.dumps(report, indent=1) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')
    elif a.camera:
        H15.write_text(camera_file(report))
        print(f'wrote {H15.relative_to(ROOT)}')
    elif a.check:
        if not roof.close(json.loads(REPORT.read_text()), report):
            sys.exit(f'{REPORT.relative_to(ROOT)} is stale: re-run with --write and review the change')
        if not roof.close(json.loads(H15.read_text()), json.loads(camera_file(report)), 0.01):
            sys.exit(f'{H15.relative_to(ROOT)} is not the stable_level fit: re-run with --camera and re-render the view')
        print('stable-end reading re-derived: matches the committed report and HABS 15\'s camera')


if __name__ == '__main__':
    main()
