#!/usr/bin/env python3
"""T-2758: is the ~2 ft by which HABS photograph 1 reads Glessner's stable roof low
the camera or the roof?

Both committed cameras that see the stable were fitted somewhere else. Photograph 1's
(`habs-01-northwest`) is a whole-house camera: its only vertical controls are the
grade and eave at the Prairie corner (W 0), 141 ft east of the stable, and every
control lies in the one north-face plane. The Cornell view's
(`cornell-northwest-west-windows`) is a west-wall homography fitted to two eave
heights that are themselves reconstructed (25.2 / 16.5 ft). Neither has a measured
length at the stable.

The carriage doorway is one: W 134.9-147.0 (sheet 2) and 12.6 ft from grade to the
soffit of its lintel (sheet 5), in the stable's north face (S 0). This tool picks its
corners in both photographs, re-solves each camera with that doorway added, and
reads the roof back through every fit: the north gable's coping apex (S 0 plane),
the cupola's pyramid apex (where its ray crosses the ridge plane W 141, and its
height on the model's centre S 14.6) and, in the Cornell view, the west gable's apex
(W 161.25 plane). It never fits a roof point and never changes the house.

    python3 tools/glessner_stable_roof_read.py            # print the table
    python3 tools/glessner_stable_roof_read.py --write    # and write the report
    python3 tools/glessner_stable_roof_read.py --check    # re-derive; fail on drift

The report is data/comparisons/glessner/stable-roof-heights.json. A dated reading,
not a per-commit gate (like T-2470's north-tower review).
"""
from pathlib import Path
import argparse, hashlib, json, math, sys
import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / 'data/reference_views/glessner_house'
REPORT = ROOT / 'data/comparisons/glessner/stable-roof-heights.json'
FT = 0.3048

# Hand picks, in each photograph's own committed pixels (about +/-2 px on photograph
# 1's 1800 x 1289 web copy, +/-5 px on the Cornell 1800 x 1305 museum copy, whose
# jambs show their east reveals from a west-standing camera).
HABS01_DOOR = [  # (W, S, z ft ng) -> (u, v)
    ((134.9, 0, 12.6), (1165, 720.7)),   # east jamb at the soffit
    ((147.0, 0, 12.6), (1323, 718.3)),   # west jamb at the soffit
    ((134.9, 0, 0.0), (1165, 895.0)),    # east jamb at the threshold
    ((147.0, 0, 0.0), (1323, 893.0)),    # west jamb at the threshold
]
HABS01_READS = {
    'gable_coping_apex': (1240, 357),    # where the coping's two slopes meet
    'gable_apex_stone_top': (1240, 350.5),
    'cupola_apex': (1313.75, 305),       # the pyramid's point, under the finial knob
}
CORNELL_OBS = [  # kind, (W, S, z), (u, v)
    ('uv', (161.25, 0, 0), (1091, 1132)),      # NW corner at grade (committed pick)
    ('uv', (161.25, 59.75, 0), (1705, 1090)),  # SW corner at grade (committed pick)
    ('edge', (161.25, 0, None), (1093, 488)),  # NW corner's arris, high up
    ('edge', (161.25, 59.75, None), (1691, 809)),
    ('uv', (134.9, 0, 12.6), (612, 816)),      # doorway east jamb at the soffit
    ('uv', (134.9, 0, 0.0), (608, 1090)),      # doorway east jamb at the threshold
    ('soffit', (None, 0, 12.6), (790, 810)),   # the soffit beside the pole (west jamb hidden)
    ('edge', (137.5, 0, None), (657.5, 640)),  # loft opening's jambs (sheet 3 plan)
    ('edge', (144.7, 0, None), (769, 630)),
]
CORNELL_READS = {
    'gable_coping_apex': (711, 217),
    'gable_apex_stone_top': (710, 209),
    'cupola_apex': (915, 135),
    'west_gable_apex': (1308, 196),        # the committed camera's own check pick
}
CORNELL_WEST_WINDOWS = {  # the committed camera's withheld checks, read again on W 161.25
    'upper north': (1246, 554), 'upper south': (1347, 601),
    'lower north': (1237, 855), 'lower south': (1397, 879),
}


def world(W, S, z):
    return np.array([(161.25 - W) * FT, (74 - S) * FT, z * FT])


def axes(yaw, pitch, roll):
    f = np.array([math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), math.sin(pitch)])
    r0 = np.array([math.cos(yaw), -math.sin(yaw), 0.])
    u0 = np.cross(r0, f)
    return np.array([r0 * math.cos(roll) + u0 * math.sin(roll), u0 * math.cos(roll) - r0 * math.sin(roll), f])


class Cam:
    def __init__(self, eye, basis, f, c, aspect=1.0):
        self.eye, self.B, self.f, self.c, self.a = np.asarray(eye, float), np.asarray(basis, float), f, c, aspect

    @classmethod
    def committed(cls, d):
        if d.get('basis_right_up_forward'):
            B = d['basis_right_up_forward']
        else:
            B = axes(math.radians(d['yaw_deg']), 0., 0.)
        return cls(d['eye'], B, d['focal_px'], tuple(d['principal_px']), d.get('pixel_aspect', 1.0))

    def project(self, P):
        q = self.B @ (P - self.eye)
        return np.array([self.c[0] + self.a * self.f * q[0] / q[2], self.c[1] - self.f * q[1] / q[2]])

    def ray(self, px):
        return self.B.T @ np.array([(px[0] - self.c[0]) / (self.a * self.f), -(px[1] - self.c[1]) / self.f, 1.])

    def on_plane(self, px, axis, value):
        """(W, S, z) where the pixel's ray crosses the plane S = value or W = value."""
        d = self.ray(px)
        i, target = (1, (74 - value) * FT) if axis == 'S' else (0, (161.25 - value) * FT)
        p = self.eye + (target - self.eye[i]) / d[i] * d
        return [round(161.25 - p[0] / FT, 2), round(74 - p[1] / FT, 2), round(p[2] / FT, 2)]

    def z_on_edge(self, W, S, v):
        lo, hi = -60., 200.
        for _ in range(60):
            mid = (lo + hi) / 2
            if self.project(world(W, S, mid))[1] > v:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    def px_per_ft(self, W, S, z):
        return self.f * FT / (self.B[2] @ (world(W, S, z) - self.eye))

    def record(self):
        return {'eye': [round(x, 4) for x in self.eye], 'basis_right_up_forward': [[round(x, 6) for x in r] for r in self.B],
                'focal_px': round(self.f, 2), 'principal_px': [round(x, 2) for x in self.c], 'pixel_aspect': round(self.a, 4)}


def residuals(cam, obs):
    out = []
    for kind, (W, S, z), (u, v) in obs:
        if kind == 'uv':
            p = cam.project(world(W, S, z))
            out += [p[0] - u, p[1] - v]
        elif kind == 'u':       # horizontal-only control: a plan position on the face
            out.append(cam.project(world(W, S, 10.))[0] - u)
        elif kind == 'edge':    # a point somewhere up a vertical arris or jamb at (W, S)
            out.append(cam.project(world(W, S, cam.z_on_edge(W, S, v)))[0] - u)
        elif kind == 'soffit':  # a point on the soffit line (z known) at an unknown W
            Wp, Sp, _ = cam.on_plane((u, v), 'S', S)
            out.append(cam.project(world(Wp, Sp, z))[1] - v)
    return np.array(out)


def fit(build, x0, obs):
    s = least_squares(lambda x: residuals(build(x), obs), x0, x_scale='jac')
    cam = build(s.x)
    r = residuals(cam, obs)
    return cam, r


def model_heights():
    form = json.loads((ROOT / 'data/structures/glessner_house.json').read_text())['phases'][0]['form']
    ridge, turret = form['ridge_west_wing']['value'], form['turret_stable']['value']
    parapet = form['gable_west_wing_north']['value']['parapet_ft']
    assert ridge['ridge'][1] == turret['apex'][1] == 'ng'
    return {'ridge_W': ridge['W'], 'ridge_ft': ridge['ridge'][0], 'gable_coping_apex_ft': round(ridge['ridge'][0] + parapet, 2),
            'cupola_centre_WS': [turret['centre_W'], turret['centre_S']], 'cupola_apex_ft': turret['apex'][0]}


def reads(cam, picks, model):
    W0, S0 = model['cupola_centre_WS']
    out = {}
    for name, px in picks.items():
        if name.startswith('gable'):
            out[name] = cam.on_plane(px, 'S', 0)
        elif name == 'cupola_apex':
            out['cupola_apex_on_ridge_plane'] = cam.on_plane(px, 'W', W0)
            out['cupola_apex_at_model_centre_S'] = cam.on_plane(px, 'S', S0)
        elif name == 'west_gable_apex':
            out[name] = cam.on_plane(px, 'W', 161.25)
    return out


def habs01(model):
    d = json.loads((VIEWS / 'habs-01-northwest.json').read_text())
    committed = Cam.committed(d)
    base = [('uv', (W, 0, z), (u, v)) if v is not None else ('u', (W, 0, None), (u, None))
            for W, z, u, v in d['solve']['controls']]
    door = [('uv', w, p) for w, p in HABS01_DOOR]
    cx, eye, h = d['principal_px'][0], d['eye'], d['eye'][2]
    yaw0, f0, cy0 = math.radians(d['yaw_deg']), d['focal_px'], d['principal_px'][1]
    variants = {
        'committed': ('the committed whole-house camera, unchanged', None, None, base),
        'doorway': ('level, eye 1.8 m (as committed); committed controls + the doorway',
                    lambda x: Cam([x[0], x[1], h], axes(x[2], 0, 0), x[3], (cx, x[4])), [eye[0], eye[1], yaw0, f0, cy0], base + door),
        'doorway_eye_height': ('as doorway, eye height free',
                               lambda x: Cam([x[0], x[1], x[5]], axes(x[2], 0, 0), x[3], (cx, x[4])), [eye[0], eye[1], yaw0, f0, cy0, h], base + door),
        'doorway_lean': ('as doorway, image lean (roll) free',
                         lambda x: Cam([x[0], x[1], h], axes(x[2], 0, x[5]), x[3], (cx, x[4])), [eye[0], eye[1], yaw0, f0, cy0, 0.], base + door),
        'doorway_aspect': ('as doorway, pixel aspect free',
                           lambda x: Cam([x[0], x[1], h], axes(x[2], 0, 0), x[3], (cx, x[4]), x[5]), [eye[0], eye[1], yaw0, f0, cy0, 1.], base + door),
    }
    form = json.loads((ROOT / 'data/structures/glessner_house.json').read_text())['phases'][0]['form']
    t, plan = form['tower_north']['value'], form['tower_north_plan']['value']
    tip = world(plan['centre_W'], plan['centre_S'], t['apex'][0] + t['finial_ft'])
    out = {}
    for key, (why, build, x0, obs) in variants.items():
        cam, r = (committed, residuals(committed, obs)) if build is None else fit(build, x0, obs)
        door_r = residuals(cam, door)
        tq = cam.project(tip)
        out[key] = {'what': why, 'fitted_obs': int(len(r)), 'rms_px': round(float(np.sqrt(np.mean(r ** 2))), 2),
                    'max_px': round(float(np.abs(r).max()), 1),
                    'doorway_rms_px': round(float(np.sqrt(np.mean(door_r ** 2))), 2),
                    'north_tower_finial_error_px': round(math.hypot(tq[0] - 428, tq[1] - 460), 1),
                    'px_per_ft_at_doorway': round(cam.px_per_ft(141, 0, 6.3), 2),
                    'reads': reads(cam, HABS01_READS, model), 'camera': cam.record()}
    # The doorway as a ruler, no camera at all: a level camera keeps one vertical
    # scale up one vertical line, and the apex stands over the doorway's middle.
    thr = (HABS01_DOOR[2][1][1] + HABS01_DOOR[3][1][1]) / 2
    sof = (HABS01_DOOR[0][1][1] + HABS01_DOOR[1][1][1]) / 2
    ruler = {name: round((thr - HABS01_READS[name][1]) / (thr - sof) * 12.6, 2) for name in ('gable_coping_apex', 'gable_apex_stone_top')}
    return out, {'threshold_v': thr, 'soffit_v': sof, 'px_per_ft': round((thr - sof) / 12.6, 2), 'reads_ft': ruler}


def cornell(model):
    d = json.loads((VIEWS / 'cornell-northwest-west-windows.json').read_text())
    committed = Cam.committed(d)
    e = d['eye']
    fw = np.array(d['basis_right_up_forward'][2])
    yaw0, pitch0 = math.atan2(fw[0], fw[1]), math.asin(fw[2])
    W, H = d['image_px']
    variants = {
        'committed': ('the committed west-wall homography on reconstructed eaves, unchanged', None, None),
        'roof_pitched': ('pose, focal, pitch and roll free; principal point at the image centre',
                         lambda x: Cam(x[:3], axes(x[3], x[4], x[5]), x[6], (W / 2, H / 2)), [e[0], e[1], e[2], yaw0, pitch0, 0., d['focal_px']]),
        'roof_level': ('pose, focal and roll free, level (a view camera\'s rising front: principal height free)',
                       lambda x: Cam(x[:3], axes(x[3], 0., x[4]), x[5], (W / 2, x[6])), [e[0], e[1], e[2], yaw0, 0., d['focal_px'], d['principal_px'][1]]),
    }
    out = {}
    for key, (why, build, x0) in variants.items():
        cam, r = (committed, residuals(committed, CORNELL_OBS)) if build is None else fit(build, x0, CORNELL_OBS)
        rec = {'what': why, 'fitted_obs': int(len(r)), 'rms_px': round(float(np.sqrt(np.mean(r ** 2))), 2),
               'max_px': round(float(np.abs(r).max()), 1), 'px_per_ft_at_doorway': round(cam.px_per_ft(141, 0, 6.3), 2),
               'reads': reads(cam, CORNELL_READS, model),
               'west_windows_on_W161_25': {k: cam.on_plane(px, 'W', 161.25)[1:] for k, px in CORNELL_WEST_WINDOWS.items()},
               'camera': cam.record()}
        if key == 'committed':
            rec['note'] = 'rms is against the doorway and north-face controls this camera was never fitted to'
        out[key] = rec
    return out


def derive():
    model = model_heights()
    h, ruler = habs01(model)
    c = cornell(model)
    def span(values):
        return [round(min(values), 2), round(max(values), 2)]
    fitted_h = [v for k, v in h.items() if k != 'committed']
    fitted_c = [v for k, v in c.items() if k != 'committed']
    summary = {
        'gable_coping_apex_ft': {'model': model['gable_coping_apex_ft'],
                                 'habs01_committed': h['committed']['reads']['gable_coping_apex'][2],
                                 'habs01_doorway_fits': span([v['reads']['gable_coping_apex'][2] for v in fitted_h]),
                                 'habs01_doorway_ruler': ruler['reads_ft']['gable_coping_apex'],
                                 'cornell_committed': c['committed']['reads']['gable_coping_apex'][2],
                                 'cornell_roof_fits': span([v['reads']['gable_coping_apex'][2] for v in fitted_c])},
        'cupola_apex_ft_at_model_centre': {'model': model['cupola_apex_ft'],
                                           'habs01_committed': h['committed']['reads']['cupola_apex_at_model_centre_S'][2],
                                           'habs01_doorway_fits': span([v['reads']['cupola_apex_at_model_centre_S'][2] for v in fitted_h]),
                                           'cornell_committed': c['committed']['reads']['cupola_apex_at_model_centre_S'][2],
                                           'cornell_roof_fits': span([v['reads']['cupola_apex_at_model_centre_S'][2] for v in fitted_c])},
        'cupola_centre_S_on_ridge_plane': {'model': model['cupola_centre_WS'][1],
                                           'habs01_committed': h['committed']['reads']['cupola_apex_on_ridge_plane'][1],
                                           'habs01_doorway_fits': span([v['reads']['cupola_apex_on_ridge_plane'][1] for v in fitted_h]),
                                           'cornell_committed': c['committed']['reads']['cupola_apex_on_ridge_plane'][1],
                                           'cornell_roof_fits': span([v['reads']['cupola_apex_on_ridge_plane'][1] for v in fitted_c])},
    }
    return {
        'ticket': 'T-2758',
        'not_a_reading': 'A bounded re-reading of two catalogued photographs through re-solved cameras; no roof point is fitted and no geometry changes.',
        'sources': {'habs01': 'habs_glessner_photo_01_nw_1963', 'cornell': 'cornell_adw_glessner_stable_1887',
                    'doorway': 'habs_glessner_house_il_1015_drawings (sheet 2 jambs W 134.9-147.0; sheet 5 soffit 12.6 ft)'},
        'camera_sha256': {n: hashlib.sha256((VIEWS / f'{n}.json').read_bytes()).hexdigest()
                          for n in ('habs-01-northwest', 'cornell-northwest-west-windows')},
        'model': model,
        'picks': {'habs01_doorway': HABS01_DOOR, 'habs01_reads': HABS01_READS,
                  'cornell_controls': CORNELL_OBS, 'cornell_reads': CORNELL_READS, 'cornell_west_windows': CORNELL_WEST_WINDOWS},
        'habs01': h, 'habs01_doorway_ruler': ruler, 'cornell': c, 'summary': summary,
    }


def close(a, b, tol=0.05):
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(close(a[k], b[k], tol) for k in a)
    if isinstance(a, (list, tuple)):
        return isinstance(b, (list, tuple)) and len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= tol
    return a == b


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--write', action='store_true')
    g.add_argument('--check', action='store_true')
    a = ap.parse_args()
    report = json.loads(json.dumps(derive()))
    for k, v in report['summary'].items():
        print(k, json.dumps(v))
    for photo in ('habs01', 'cornell'):
        for key, v in report[photo].items():
            print(f"{photo}.{key}: rms {v['rms_px']} px (max {v['max_px']}) over {v['fitted_obs']}; {v['px_per_ft_at_doorway']} px/ft at the doorway")
    if a.write:
        REPORT.write_text(json.dumps(report, indent=1) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')
    elif a.check:
        committed = json.loads(REPORT.read_text())
        if not close(committed, report):
            sys.exit(f'{REPORT.relative_to(ROOT)} is stale: re-run with --write and review the change')
        print('stable-roof reading re-derived: matches the committed report')


if __name__ == '__main__':
    main()
