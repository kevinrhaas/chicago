#!/usr/bin/env python3
"""T-3102: which of T-2758's two Cornell cameras holds on the stable's roof?

T-2758 re-solved the Cornell print (cornell_adw_glessner_stable_1887) two ways on the
same 13 controls: `roof_pitched` (tilted, principal point at the image centre) and
`roof_level` (level, a view camera's rising front: principal height free). T-3096 found
them 0.46-0.49 m apart on the alley-end roll foot. Every control lies on the stable's
walls between grade and about 25 ft, so the two are the ends of one valley: tilting the
camera and raising the lens move the walls the same way and the roof differently.

This walks that valley at pinned tilts, 0-9 degrees, every other parameter of the
roof_level fit free, and reads three things at each tilt:

1. how well the 13 controls fit (they cannot tell the tilts apart);
2. the roof, through T-2758's own picks and read rules: the north gable's coping apex,
   the cupola's apex at the model's centre, the west gable's apex;
3. the print's plumb lines: three downpipes tracked down the image, against the lean each
   camera gives a plumb line at the same pixel.

and sets (2) against HABS photograph 1, the only other photograph of the same rigid
roof, read through T-2758's doorway fits. No roof point is fitted and nothing in the
house changes.

    python3 docs/RESEARCH/glessner-cornell-fits-T-3102/read_fits.py           # print
    python3 docs/RESEARCH/glessner-cornell-fits-T-3102/read_fits.py --write   # and write readings.json
    python3 docs/RESEARCH/glessner-cornell-fits-T-3102/read_fits.py --check   # re-derive; fail on drift
"""
from pathlib import Path
import argparse, json, math, sys
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import glessner_stable_roof_read as g  # noqa: E402
import glessner_cupola_read as cr  # noqa: E402  (T-3031's cupola fit)

VIEW = ROOT / 'data/reference_views/glessner_house/cornell-northwest-west-windows.json'
T2758 = ROOT / 'data/comparisons/glessner/stable-roof-heights.json'
OUT = HERE / 'readings.json'
TILTS = range(10)
COPING_TOL_FT = 0.3

# The print's plumb lines, in its committed 1800 x 1305 pixels: (name, what, kind, u0, v0, v1).
# 'dark' follows the darkest column (a pipe against stone); +1 / -1 follow the strongest
# rising / falling step across the row (an arris against the sky or a darker mass). Two edges
# were tried and left out because their lean moved with the search window: the house
# chimney's east arris at u 110 (+0.017 to +0.057; only 100 rows clear against the sky) and
# the dark mass beyond the stable at u 1775 (its trace slides off the edge onto the brick
# below). The three pipes hold to 0.003 at every window from 6 to 12 px.
LINES = [
    ('pipe_east', 'downpipe at the foot of the north gable, east of the carriage door', 'dark', 497, 610, 930),
    ('pipe_nw', 'downpipe on the stable\'s NW corner', 'dark', 1085, 500, 1120),
    ('pipe_west', 'downpipe on the west wall at the south gable\'s foot', 'dark', 1495, 780, 1095),
]


def track(im, kind, u0, v0, v1, half=8):
    """Follow the line from (u0, v0) down to v1, re-centring the search window on each
    row's find, so a lean never walks the line out of a fixed window."""
    pts, u = [], float(u0)
    for v in range(v0, v1, 4):
        c = int(round(u))
        row = im[v - 1:v + 2, c - half:c + half + 1].mean(0)
        if kind == 'dark':
            k = np.convolve(row, np.ones(5) / 5, 'same')
            i = int(np.argmin(k[2:-2])) + 2
            w = np.clip(k.max() - k, 0, None)
            lo, hi = max(i - 4, 0), min(i + 5, len(k))
            x = (w[lo:hi] * np.arange(lo, hi)).sum() / w[lo:hi].sum()
        else:
            k = np.gradient(np.convolve(row, np.ones(3) / 3, 'same')) * kind
            k[:2] = k[-2:] = 0
            i = int(np.argmax(k))
            dd = k[i - 1] - 2 * k[i] + k[i + 1]
            x = i + (0.5 * (k[i - 1] - k[i + 1]) / dd if dd else 0.)
        u = c - half + x
        pts.append((v, u))
    p = np.array(pts)
    a, b = np.polyfit(p[:, 0], p[:, 1], 1)
    r = p[:, 1] - (a * p[:, 0] + b)
    vm = (v0 + v1) / 2
    se = float(np.sqrt((r ** 2).sum() / (len(p) - 2)) / np.sqrt(((p[:, 0] - p[:, 0].mean()) ** 2).sum()))
    return {'at_px': [round(a * vm + b, 1), vm], 'du_dv': round(float(a), 4), 'std_err': round(se, 4),
            'track_rms_px': round(float(np.sqrt((r ** 2).mean())), 2), 'samples': len(p)}


def lean(cam, u, v):
    """du/dv of a plumb line through pixel (u, v) (negative: it leans right going up)."""
    q = cam.B @ np.array([0., 0., 1.])
    return (cam.a * cam.f * q[0] + (cam.c[0] - u) * q[2]) / (-cam.f * q[1] + (cam.c[1] - v) * q[2])


def roof(cam, model):
    rd = g.reads(cam, g.CORNELL_READS, model)
    return {'gable_coping_apex_ft': rd['gable_coping_apex'][2], 'cupola_apex_ft_at_model_centre': rd['cupola_apex_at_model_centre_S'][2],
            'cupola_centre_S_on_ridge_plane': rd['cupola_apex_on_ridge_plane'][1], 'west_gable_apex_ft': rd['west_gable_apex'][2]}


def plumb(cam, lines):
    out = {n: round(float(lean(cam, *l['at_px'])), 4) for n, l in lines.items()}
    res = [out[n] - l['du_dv'] for n, l in lines.items()]
    return out, round(float(np.sqrt(np.mean(np.square(res)))), 4)


def derive():
    d = json.loads(VIEW.read_text())
    im = np.asarray(Image.open(VIEW.parent / d['photo']).convert('L'), float)
    lines = {n: dict(what=w, **track(im, k, u0, v0, v1)) for n, w, k, u0, v0, v1 in LINES}
    model = g.model_heights()
    e = d['eye']
    fw = np.array(d['basis_right_up_forward'][2])
    yaw0, (W, H) = math.atan2(fw[0], fw[1]), d['image_px']
    t31 = cr.built(cr.record())
    start = [t31[k] for k in ('half_ft', 'overhang_ft', 'eave_ft', 'apex_ft', 'centre_S')]
    habs_cam = cr.cameras()[0]['habs01']
    valley = {}
    for t in TILTS:
        p = math.radians(t)
        cam, r = g.fit(lambda x: g.Cam(x[:3], g.axes(x[3], p, x[4]), x[5], (W / 2, x[6])),
                       [e[0], e[1], e[2], yaw0, 0., d['focal_px'], d['principal_px'][1]], g.CORNELL_OBS)
        leans, lrms = plumb(cam, lines)
        valley[f'{t}deg'] = {'controls_rms_px': round(float(np.sqrt(np.mean(r ** 2))), 2), 'principal_v_px': round(cam.c[1], 1),
                             'focal_px': round(cam.f, 1), 'roof': roof(cam, model), 'plumb_lean': leans, 'plumb_rms': lrms,
                             'camera': cam.record()}
        cams = {'habs01': habs_cam, 'cornell': (cam, np.array(cr.ANCHOR['cornell']) - cam.project(g.world(cr.RIDGE_W, 0, model['gable_coping_apex_ft'])))}
        alone, joint = cr.fit(cams, ['cornell'], start), cr.fit(cams, ['habs01', 'cornell'], start)
        valley[f'{t}deg']['cupola_t3031'] = {'cornell_alone': alone['params'], 'cornell_alone_rms_px': alone['rms_px'],
                                             'joint': joint['params'], 'joint_rms_px': joint['rms_px']}
    # T-2758's two fits as committed, read the same way.
    rep = json.loads(T2758.read_text())
    fits = {}
    for k in ('roof_pitched', 'roof_level'):
        c = rep['cornell'][k]
        cam = g.Cam(c['camera']['eye'], c['camera']['basis_right_up_forward'], c['camera']['focal_px'],
                    tuple(c['camera']['principal_px']), c['camera']['pixel_aspect'])
        leans, lrms = plumb(cam, lines)
        fits[k] = {'tilt_deg': round(math.degrees(math.asin(cam.B[2][2])), 2), 'controls_rms_px': c['rms_px'],
                   'roof': roof(cam, model), 'plumb_lean': leans, 'plumb_rms': lrms}
    # HABS photograph 1 through T-2758's fitted cameras (committed is the whole-house camera, not a fit).
    h = {k: v for k, v in rep['habs01'].items() if k != 'committed'}
    span = lambda xs: [round(min(xs), 2), round(max(xs), 2)]
    habs = {'gable_coping_apex_ft': span([v['reads']['gable_coping_apex'][2] for v in h.values()]),
            'cupola_apex_ft_at_model_centre': span([v['reads']['cupola_apex_at_model_centre_S'][2] for v in h.values()]),
            'cupola_centre_S_on_ridge_plane': span([v['reads']['cupola_apex_on_ridge_plane'][1] for v in h.values()]),
            'doorway_ruler_coping_ft': rep['habs01_doorway_ruler']['reads_ft']['gable_coping_apex']}
    # Which tilts put this print's coping apex where HABS 1's fits put it, to the picks'
    # tolerance: +/-2 px at about 14 px/ft on HABS 1 and +/-5 px at about 23 px/ft here, so
    # about 0.15 + 0.22 ft, taken as 0.3. The coping is the check because it lies on the
    # doorway's own face (S 0), where both cameras were fitted. The cupola is read and not
    # gated: its place on S is not settled (HABS 1's fits put it at S 10.4-14.4), and a
    # height read at the model's S 14.6 moves with that place.
    lo, hi = habs['gable_coping_apex_ft'][0] - COPING_TOL_FT, habs['gable_coping_apex_ft'][1] + COPING_TOL_FT
    agree = [t for t in TILTS if lo <= valley[f'{t}deg']['roof']['gable_coping_apex_ft'] <= hi]
    best = min(TILTS, key=lambda t: valley[f'{t}deg']['plumb_rms'])
    # the plumb lines' minimum between whole degrees (a parabola through its three nearest)
    r0, r1, r2 = (valley[f'{t}deg']['plumb_rms'] for t in (best - 1, best, best + 1))
    best_fine = round(best + 0.5 * (r0 - r2) / (r0 - 2 * r1 + r2), 1)
    return {
        'ticket': 'T-3102',
        'not_a_reading': 'A re-reading of the Cornell print through T-2758\'s controls at pinned tilts; no roof point is fitted and no geometry changes.',
        'sources': {'cornell': 'cornell_adw_glessner_stable_1887', 'habs01': 'habs_glessner_photo_01_nw_1963', 'fits': 'data/comparisons/glessner/stable-roof-heights.json (T-2758)'},
        'model': model, 'cupola_as_built': t31, 'plumb_lines': lines, 't2758_fits': fits, 'valley': valley, 'habs01_doorway_fits': habs,
        'verdict': {'coping_window_ft': [round(lo, 2), round(hi, 2)], 'tilts_where_the_coping_agrees_with_habs01_deg': agree,
                    'tilt_the_plumb_lines_prefer_deg': best_fine,
                    'controls_rms_span_px': span([v['controls_rms_px'] for v in valley.values()])},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    m = ap.add_mutually_exclusive_group()
    m.add_argument('--write', action='store_true')
    m.add_argument('--check', action='store_true')
    a = ap.parse_args()
    rep = json.loads(json.dumps(derive()))
    for n, l in rep['plumb_lines'].items():
        print(f"{n:10s} du/dv {l['du_dv']:+.4f} +/- {l['std_err']:.4f} at u {l['at_px'][0]:.0f} (track rms {l['track_rms_px']} px)")
    for k, v in list(rep['t2758_fits'].items()) + list(rep['valley'].items()):
        r = v['roof']
        print(f"{k:12s} controls {v['controls_rms_px']:5.2f} px  coping {r['gable_coping_apex_ft']:.2f}  cupola {r['cupola_apex_ft_at_model_centre']:.2f}"
              f"  west gable {r['west_gable_apex_ft']:.2f}  plumb rms {v['plumb_rms']:.4f}")
        if 'cupola_t3031' in v:
            cu = v['cupola_t3031']
            print(f"{'':12s} T-3031 cupola, joint: eave {cu['joint']['eave_ft']:.2f} apex {cu['joint']['apex_ft']:.2f} S {cu['joint']['centre_S']:.2f}"
                  f" rms {cu['joint_rms_px']:.2f}; Cornell alone rms {cu['cornell_alone_rms_px']:.2f}")
    print('habs01', json.dumps(rep['habs01_doorway_fits']))
    print('verdict', json.dumps(rep['verdict']))
    if a.write:
        OUT.write_text(json.dumps(rep, indent=1) + '\n')
        print(f'wrote {OUT.relative_to(ROOT)}')
    elif a.check:
        if not g.close(json.loads(OUT.read_text()), rep):
            sys.exit(f'{OUT.relative_to(ROOT)} is stale: re-run with --write and review the change')
        print('T-3102 reading re-derived: matches readings.json')


if __name__ == '__main__':
    main()
