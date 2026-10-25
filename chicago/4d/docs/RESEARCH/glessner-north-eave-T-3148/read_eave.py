#!/usr/bin/env python3
"""T-3148: is Glessner's north-face eave level either side of the stable's 18th Street gable?

T-3147 found, through HABS 15's refitted camera, the print's eave about level both sides of
the stable gable where the build stepped from 23.1 ft east of it to 25.2 ft west of it
(`stable_roof_rework.north_west_eave`, T-2231). This reads the tiles' lower edge in HABS
photographs 1 and 15 at stations along the north face (S 0) and asks two things:

1. CAMERA-FREE. A level line on one plane face projects to one straight image line through
   any pinhole. Fit the line the edge draws along the 18th Street range east of the gable
   (W 60-124, where sheet 4 measures the eave at 23.1 ft) and read how far the edge west of
   the gable (W 156-160) stands off its extension. A 2.1 ft step would stand about 30 px off.
2. THROUGH THE STABLE-FITTED CAMERAS (T-2758's HABS 01 doorway fit, eye height free;
   T-3147's HABS 15 stable_level fit): the edge's height on the face plane at each station.

Picks: each column is the mean of 5 px across, read off its brightness profile -- the tiles'
last course is a dark line over the bright gutter, which drops into the dark wall shadow.
`tile_end` is that dark line's centre, `gutter_foot` the bright-to-dark step under it
(about +/-1 px).

    python3 docs/RESEARCH/glessner-north-eave-T-3148/read_eave.py   # readings.json, habs01-eave-line.jpg
"""
from pathlib import Path
import json, sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from glessner_stable_roof_read import Cam, world, VIEWS  # noqa: E402

PHOTOS = ROOT.parent / 'prairie_1904_v1/research/public'
# (W ft, tile_end v, gutter_foot v), u is where the station's W projects on the face.
H01 = [(60, 635.5, 641), (80, 620, 626), (100, 602.5, 608.5), (120, 581.5, 589), (124, 577.5, 585),
       (156, 531.5, 539.5), (158, 529, 537.5), (160, 525.5, 535)]
H15 = [(118, 276, 285.5), (121, 276.5, 286.5), (124, 277.5, 286.5),
       (156, 279, 287.5), (158, 280.5, 289), (160, 280.5, 290.5)]
GABLE = (127.75, 154.25)  # stable_north_gable W, the gable's feet
# The c. 1887 Cornell print (cornell-northwest-west-windows), camera-free only: its committed
# camera is a west-wall homography 18 px off at the roof (T-2758), so no height is read through
# it, and it gives only the scale of the step. (u, v) where the tiles' last course first turns
# dark over the gutter, east of the gable (u 230-450, W about 103-118) and west of it.
CORNELL_EAST = [(230, 643.5), (300, 629.0), (380, 612.5), (450, 598.0)]
CORNELL_WEST = [(980, 485.0), (1030, 473.5), (1070, 466.0)]


def cameras():
    rep = json.loads((ROOT / 'data/comparisons/glessner/stable-end.json').read_text())
    c = rep['habs01']['doorway_eye_height']['camera']
    h01 = Cam(c['eye'], c['basis_right_up_forward'], c['focal_px'], tuple(c['principal_px']), c.get('pixel_aspect', 1.0))
    h15 = Cam.committed(json.loads((VIEWS / 'habs-15-stable-detail.json').read_text()))
    return {'habs01': (h01, 'habs_glessner_photo_01_nw_1963', 'T-2758 doorway_eye_height (data/comparisons/glessner/stable-end.json)', H01),
            'habs15': (h15, 'habs_glessner_photo_15_north_stable_1965', 'T-3147 stable_level (habs-15-stable-detail.json)', H15)}


def read(cam, picks):
    rows, east, west = [], [], []
    for W, t, g in picks:
        u = float(cam.project(world(W, 0, 23.1))[0])
        row = {'W': W, 'u': round(u, 1), 'tile_end_v': t, 'gutter_foot_v': g,
               'tile_end_face_ft': round(float(cam.z_on_edge(W, 0, t)), 2),
               'gutter_foot_face_ft': round(float(cam.z_on_edge(W, 0, g)), 2)}
        rows.append(row)
        (east if W < GABLE[0] else west).append(row)
    out = {'stations': rows}
    for key in ('tile_end', 'gutter_foot'):
        a, b = np.polyfit([r['u'] for r in east], [r[f'{key}_v'] for r in east], 1)
        off = [round(r[f'{key}_v'] - (a * r['u'] + b), 1) for r in west]
        # what a step of 25.2 - 23.1 ft west of the gable would draw there, in px
        step = [round(float(cam.project(world(r['W'], 0, 23.1))[1] - cam.project(world(r['W'], 0, 25.2))[1]), 1) for r in west]
        out[f'{key}_line'] = {'fitted_on_W': [r['W'] for r in east], 'slope_px_per_px': round(float(a), 5),
                              'east_rms_px': round(float(np.sqrt(np.mean([(r[f'{key}_v'] - (a * r['u'] + b)) ** 2 for r in east]))), 2),
                              'west_off_line_px': off, 'a_2_1_ft_step_would_be_px': step}
        e = [r[f'{key}_face_ft'] for r in east]; w = [r[f'{key}_face_ft'] for r in west]
        out[f'{key}_face_ft'] = {'east_of_gable': [min(e), max(e)], 'west_of_gable': [min(w), max(w)],
                                 'west_minus_east_mean': round(float(np.mean(w) - np.mean(e)), 2)}
    return out


def figure(cam, picks, line):
    from PIL import Image, ImageDraw
    im = Image.open(PHOTOS / 'glessner-habs-photo-01.jpg').convert('RGB')
    x0, y0, x1, y1 = 420, 470, 1600, 680
    im = im.crop((x0, y0, x1, y1))
    d = ImageDraw.Draw(im)
    a, b = line
    d.line([(0, a * x0 + b - y0), (x1 - x0, a * x1 + b - y0)], fill=(255, 210, 0), width=1)
    # blue: where the edge would run west of the gable if the eave stood at 25.2 ft there
    p, q = (cam.project(world(W, 0, 25.2)) for W in (GABLE[1], 161.25))
    lift = cam.project(world(158, 0, 23.1))[1] - cam.project(world(158, 0, 25.2))[1]
    d.line([(p[0] - x0, a * p[0] + b - y0 - lift), (q[0] - x0, a * q[0] + b - y0 - lift)], fill=(90, 160, 255), width=2)
    for W, t, _ in picks:
        u = cam.project(world(W, 0, 23.1))[0] - x0
        d.ellipse([u - 3, t - y0 - 3, u + 3, t - y0 + 3], outline=(255, 60, 60), width=2)
    im = im.resize((im.width * 3 // 2, im.height * 3 // 2))
    im.save(HERE / 'habs01-eave-line.jpg', quality=88)


def main():
    out = {'ticket': 'T-3148',
           'not_a_reading': 'A re-reading of two catalogued photographs; no camera is refitted and no building point is fitted.',
           'gable_feet_W': list(GABLE)}
    for key, (cam, source, fit, picks) in cameras().items():
        out[key] = {'source': source, 'camera': fit, **read(cam, picks)}
        print(key, json.dumps({k: v for k, v in out[key].items() if k.endswith('_line') or k.endswith('_ft')}))
    d = json.loads((VIEWS / 'cornell-northwest-west-windows.json').read_text())
    cam = Cam.committed(d)
    a, b = np.polyfit(*zip(*CORNELL_EAST), 1)
    out['cornell'] = {'source': 'cornell_adw_glessner_stable_1887', 'camera': 'none (camera-free); the committed camera only scales the step',
                      'east_picks_uv': CORNELL_EAST, 'west_picks_uv': CORNELL_WEST, 'slope_px_per_px': round(float(a), 5),
                      'east_rms_px': round(float(np.sqrt(np.mean([(v - (a * u + b)) ** 2 for u, v in CORNELL_EAST]))), 2),
                      'west_off_line_px': [round(v - (a * u + b), 1) for u, v in CORNELL_WEST],
                      'a_2_1_ft_step_would_be_px_about': round(float(cam.project(world(158, 0, 23.1))[1] - cam.project(world(158, 0, 25.2))[1]), 0)}
    print('cornell', json.dumps({k: v for k, v in out['cornell'].items() if 'px' in k}))
    (HERE / 'readings.json').write_text(json.dumps(out, indent=1) + '\n')
    cam = cameras()['habs01'][0]
    east = [r for r in out['habs01']['stations'] if r['W'] < GABLE[0]]
    figure(cam, H01, np.polyfit([r['u'] for r in east], [r['tile_end_v'] for r in east], 1))


if __name__ == '__main__':
    main()
