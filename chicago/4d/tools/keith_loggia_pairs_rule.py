#!/usr/bin/env python3
"""T-2874: Keith's loggia pairs' plan arrangement ruled between the 1965 slide, the 1888 plate and Nickel 1967.

T-2845 rebuilt the loggia at the first-floor plan's place, each pair's two shafts 0.36 m apart side by
side along the front (the 1888 plate's pitch, which its re-fitted camera draws within 2-4 px). On that
GLB the 1965 slide (a18-gh-1808-porch-1965) reads each pair about 8 px WIDER than it draws, and the
record's last open item asked whether the pairs stand staggered in depth. This reads all three pictures
that see the pairs and asks which plan of two round shafts they agree on.

  THE READS. The slide's four shaft silhouettes are T-2836's (keith_loggia_plan_rule.slide_points, read
  by luminance down rows 160-215). The plate's outer silhouettes and the dark line between each pair's
  shafts are T-2844's and T-2845's (PLATE_PAIRS, keith_loggia_built_read.PLATE_GAPS, rows 1440-1520).
  Nickel 1967 is read here (NICKEL_ROWS, mid-shaft, each pair's half-max edges against the shade either
  side). Every picture is read on its committed camera, with the pair's centre at the plan's.

  THE PLANS. Each pair is drawn as two round shafts (radius SHAFT_R at mid-shaft, 4.0 m) at the built
  place and asked four ways:
    built         side by side at 0.36 m (the GLB in the tree);
    stagger       the pair's axis turned: the north shaft forward of the south by du, centred;
    south back    the north shaft where it stands, the south shaft set back (west) by d;
    coupled       radius and pitch free, side by side, the plate's split (a whole south shaft in front,
                  a partial north one behind) held as well as the three widths.
  Each plan's silhouettes are drawn on all three cameras against the reads; widths (right minus left)
  are what a camera's own placement error cannot move, so they carry the ruling.

  python3 tools/keith_loggia_pairs_rule.py            # print the reading
  python3 tools/keith_loggia_pairs_rule.py --write    # and write REPORT

What it does not do: move the model. The ruling it records keeps the pairs as built.
"""
from pathlib import Path
import argparse, hashlib, json, sys
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import keith_loggia_plan_rule as R  # noqa: E402  T-2836's slide reads, T-2844's plate reads
import keith_loggia_built_read as B  # noqa: E402  T-2845's built place and the plate's gaps

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / 'data/reference_views/keith_house_1808_prairie'
GLB = ROOT / 'assets/gltf/keith_house_1808_prairie__as_built_1886.glb'
REPORT = ROOT / 'docs/RESEARCH/photo-match/keith_house_1808_prairie/keith-loggia-pairs-rule.json'
SLIDE, PLATE, NICKEL = 'a18-gh-1808-porch-1965', 'inland-1888', 'nickel-1967'
SHAFT_U, SHAFT_Y, SHAFT_R = 20.40, 4.0, B.SHAFT_R
PITCH = B.PITCH
NICKEL_ROWS = (660, 690)                                   # mid-shaft on nickel-1967.jpg
NICKEL_WINDOWS = {'south': (326, 352), 'north': (402, 433)}  # each pair and the shade either side
PLAN_SHAFT_PX = 7                                           # 0.31 m at the plan's 23.17 px per m


def camera(name):
    return json.loads((VIEWS / f'{name}.json').read_text())


def project(c, P):
    """The committed camera's projection: eye, yaw (or its fitted basis), focal length, principal point."""
    if 'basis_right_up_forward' in c:
        rt, up, fw = (np.array(b, float) for b in c['basis_right_up_forward'])
    else:
        y = np.radians(c['yaw_deg'])
        fw, rt, up = np.array([np.sin(y), np.cos(y), 0.]), np.array([np.cos(y), -np.sin(y), 0.]), np.array([0, 0, 1.])
    d = np.asarray(P, float) - np.asarray(c['eye'], float)
    z = d @ fw
    return c['principal_px'][0] + c['focal_px'] * (d @ rt) / z, z


def shafts(c, k, south_uv, north_uv, r):
    """Each shaft's silhouette (left, right) and depth on camera c."""
    out = []
    for u, v in (south_uv, north_uv):
        x, z = project(c, [u, v, SHAFT_Y])
        w = c['focal_px'] * r / z
        out.append({'x': (x - w, x + w), 'z': z})
    return out


def plan(kind, k, a=0.0, pitch=PITCH, r=SHAFT_R):
    v = R.centre(B.BUILT[k])
    if kind == 'stagger':        # a = du, the north shaft forward of the south, centred on the line
        return (SHAFT_U - a / 2, v - pitch / 2), (SHAFT_U + a / 2, v + pitch / 2), r
    if kind == 'south back':     # a = d, the south shaft set back, the north where it stands
        return (SHAFT_U - a, v - pitch / 2), (SHAFT_U, v + pitch / 2), r
    return (SHAFT_U, v - pitch / 2), (SHAFT_U, v + pitch / 2), r


def drawn(c, k, s_uv, n_uv, r):
    sh = shafts(c, k, s_uv, n_uv, r)
    left, right = sorted(sh, key=lambda s: s['x'][0])
    near, far = (left, right) if left['z'] < right['z'] else (right, left)
    fl, fr = far['x']
    if near['x'][0] <= fl <= near['x'][1]:
        fl = near['x'][1]
    if near['x'][0] <= fr <= near['x'][1]:
        fr = near['x'][0]
    return {'outer': (min(left['x'][0], right['x'][0]), max(left['x'][1], right['x'][1])),
            'nearer': 'left' if near is left else 'right',
            'near_px': near['x'][1] - near['x'][0], 'far_visible_px': max(0.0, fr - fl)}


def read_nickel(c):
    """Each pair's outer half-max edges: scanned inward from the window's ends, so a flute's shade
    inside the pair does not stop the read."""
    a = np.asarray(Image.open((VIEWS / c['photo']).resolve()).convert('L'), float)
    out = {}
    for k, (x0, x1) in NICKEL_WINDOWS.items():
        p = a[NICKEL_ROWS[0]:NICKEL_ROWS[1], x0:x1].mean(0)
        i = int(p.argmax())
        half_l, half_r = (p[i] + p[:i].min()) / 2, (p[i] + p[i:].min()) / 2
        j = int(np.argmax(p >= half_l))                       # first lit column from the left
        left = x0 + j - 1 + (half_l - p[j - 1]) / (p[j] - p[j - 1])
        j = len(p) - 1 - int(np.argmax(p[::-1] >= half_r))    # first lit column from the right
        right = x0 + j + (p[j] - half_r) / (p[j] - p[j + 1])
        out[k] = (round(float(left), 1), round(float(right), 1))
    return out


def reads():
    sil = {lab: x for lab, kind, _, _, x in R.slide_points(B.BUILT)[0] if kind == 'shaft'}
    slide = {'south': (sil['south pair south shaft, left silhouette'], sil['south pair north shaft, right silhouette']),
             'north': (sil['north pair south shaft, left silhouette'], sil['north pair north shaft, right silhouette'])}
    return {SLIDE: slide, PLATE: {k: tuple(v) for k, v in R.PLATE_PAIRS.items()}, NICKEL: read_nickel(camera(NICKEL))}


def table(cams, rd, kind, k, **kw):
    s_uv, n_uv, r = plan(kind, k, **kw)
    row = {}
    for n, c in cams.items():
        d = drawn(c, k, s_uv, n_uv, r)
        (l, rr), (pl, pr) = d['outer'], rd[n][k]
        row[n] = {'drawn_x': [round(l, 1), round(rr, 1)], 'read_x': [pl, pr], 'left_dx_px': round(l - pl, 1),
                  'right_dx_px': round(rr - pr, 1), 'width_dx_px': round((rr - l) - (pr - pl), 1)}
        if n == PLATE:
            row[n].update({'nearer_shaft': d['nearer'], 'near_px': round(d['near_px'], 1),
                           'far_visible_px': round(d['far_visible_px'], 1)})
    w = [row[n]['width_dx_px'] for n in cams]
    return row, round(float(np.sqrt(np.mean(np.square(w)))), 2)


def plate_split(k):
    (o0, o1), (g0, g1) = R.PLATE_PAIRS[k], B.PLATE_GAPS[k]
    return {'south_shaft_px': g0 - o0, 'north_shaft_px': o1 - g1, 'line_x': [g0, g1]}


def coupled_search(cams, rd, k):
    """Radius and pitch free (side by side); the three widths and the plate's split together."""
    sp, best = plate_split(k), None
    for r in np.arange(0.13, 0.2401, 0.005):
        for pitch in np.arange(0.0, 0.601, 0.01):
            s_uv, n_uv, _ = plan('built', k, pitch=pitch)
            e = []
            for n, c in cams.items():
                d = drawn(c, k, s_uv, n_uv, r)
                e.append((d['outer'][1] - d['outer'][0]) - (rd[n][k][1] - rd[n][k][0]))
            d = drawn(cams[PLATE], k, s_uv, n_uv, r)
            e += [d['near_px'] - sp['south_shaft_px'], d['far_visible_px'] - sp['north_shaft_px']]
            rms = float(np.sqrt(np.mean(np.square(e))))
            if best is None or rms < best[0]:
                best = (rms, round(float(r), 3), round(float(pitch), 2))
    return {'rms_px': round(best[0], 2), 'shaft_r_m': best[1], 'pitch_m': best[2]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help=f'write {REPORT.relative_to(ROOT)}')
    args = ap.parse_args()
    cams = {n: camera(n) for n in (SLIDE, PLATE, NICKEL)}
    rd = reads()
    out = {'reads': {n: {k: list(v) for k, v in rd[n].items()} for n in rd},
           'plate_split': {k: plate_split(k) for k in ('south', 'north')}, 'pairs': {}}
    print('reads', out['reads'])
    print('plate split', out['plate_split'])
    for k in ('south', 'north'):
        res = {}
        res['built'] = dict(zip(('views', 'width_rms_px'), table(cams, rd, 'built', k)))
        for du in (0.1, 0.2, 0.25, 0.3):
            res[f'stagger du {du}'] = dict(zip(('views', 'width_rms_px'), table(cams, rd, 'stagger', k, a=du)))
        for d in (0.07, 0.1, 0.15, 0.2, 0.25):
            res[f'south back {d}'] = dict(zip(('views', 'width_rms_px'), table(cams, rd, 'south back', k, a=d)))
        cp = coupled_search(cams, rd, k)
        res['coupled (best)'] = {**cp, **dict(zip(('views', 'width_rms_px'),
                                                  table(cams, rd, 'built', k, pitch=cp['pitch_m'], r=cp['shaft_r_m'])))}
        out['pairs'][k] = res
        print(k)
        for lab, v in res.items():
            vs = '  '.join(f"{n[:6]} L{x['left_dx_px']:+5.1f} R{x['right_dx_px']:+5.1f} W{x['width_dx_px']:+5.1f}"
                           for n, x in v['views'].items())
            extra = f" plate nearer {v['views'][PLATE]['nearer_shaft']} {v['views'][PLATE]['near_px']}/{v['views'][PLATE]['far_visible_px']} px"
            print(f"  {lab:18s} {vs}  rmsW {v['width_rms_px']:5.2f}{extra}")
    if args.write:
        REPORT.write_text(json.dumps({
            '_doc': 'Written by tools/keith_loggia_pairs_rule.py (T-2874): each loggia pair drawn as two round shafts '
                    'four ways on the slide\'s, the plate\'s and Nickel 1967\'s committed cameras, against the reads. '
                    'Read the tool\'s docstring; *_dx_px is drawn minus read.',
            'glb': str(GLB.relative_to(ROOT)), 'glb_sha256': hashlib.sha256(GLB.read_bytes()).hexdigest(),
            'cameras': {n: str((VIEWS / f'{n}.json').relative_to(ROOT)) for n in cams},
            'built': {k: list(v) for k, v in B.BUILT.items()}, 'pitch_m': PITCH, 'shaft_r_m': SHAFT_R,
            'nickel_rows': list(NICKEL_ROWS), 'plan_shaft_px': PLAN_SHAFT_PX, **out}, indent=1) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
