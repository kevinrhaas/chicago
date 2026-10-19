#!/usr/bin/env python3
"""T-2845: Keith's loggia read again on the GLB that builds it at the first-floor plan's place.

T-2844 (tools/keith_loggia_plan_rule.py) ruled the loggia's front pedestals off the plan under the
1888 plate, about 0.6 m across at v 6.73-7.34 and 9.58-10.23, and left building them to K07. T-2845
built them: 0.6 m square at v 6.75-7.35 and 9.6-10.2, each pair's shafts 0.36 m apart about the
pedestal's middle (they stood 0.45 m apart on the 0.9 m pedestals). This reads both pictures on the
loggia as it now stands.

  1. THE PLATE (tools/keith_plate_level_fit.py's level camera, square pixels, its 27 coordinates),
     the loggia's world points at the built place. Its camera was fitted (T-2763) with the loggia's
     capital tops, cap arrises and faces among its controls at the OLD place, so on the rebuilt GLB
     it draws both pairs about 13 px south of the print's; this fit is the camera the view takes.
     Each pair's two shafts' outer silhouettes and the dark gap between them are then predicted
     (not controls) against the print's (keith_loggia_plan_rule.PLATE_PAIRS; the gaps x 907-910
     and 1126-1129, read down rows 1440-1520).

  2. THE 1965 SLIDE (tools/keith_1965_cause_fit.py's level camera on T-2764's 29 coordinates, the
     principal heads at 4.70 m, T-2831), the shafts' silhouettes at their built pitch: with nothing
     more free (the camera the view takes), with k on the loggia's heights over its deck, with the
     loggia free to move in plan (dv), and with both. What k reads here is the column's remaining
     height factor that T-2845 rules.

  python3 tools/keith_loggia_built_read.py            # print the reading
  python3 tools/keith_loggia_built_read.py --write    # and write REPORT and both views' cameras
"""
from pathlib import Path
import argparse, hashlib, json, sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import keith_loggia_plan_rule as R  # noqa: E402  T-2844's readers and fitters
import keith_plate_level_fit as pf  # noqa: E402
import keith_1965_level_fit as lf  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'docs/RESEARCH/photo-match/keith_house_1808_prairie/keith-loggia-built-read.json'
PLATE_CAMERA = ROOT / 'data/reference_views/keith_house_1808_prairie/inland-1888.json'
BUILT = {'south': (6.75, 7.35), 'north': (9.6, 10.2)}
PITCH, SHAFT_R = 0.36, 0.155        # the record's pitch_m; the turned shaft's radius at mid-height
PLATE_GAPS = {'south': (907.0, 910.0), 'north': (1126.0, 1129.0)}


def pairs_on_plate(p, lay, pitch):
    """Each pair's outer silhouettes and the gap between its shafts, mid-shaft (4.0 m), as drawn."""
    X = lambda v: float(pf.project(p, [20.4, v, 4.0], False)[0])
    out = {}
    for k in ('south', 'north'):
        c, h = R.centre(lay[k]), pitch / 2
        outer = sorted((X(c - h - SHAFT_R), X(c + h + SHAFT_R)))
        gap = sorted((X(c - h + SHAFT_R), X(c + h - SHAFT_R)))
        out[k] = {'outer_x': [round(v, 1) for v in outer], 'print_outer_x': list(R.PLATE_PAIRS[k]),
                  'gap_x': [round(v, 1) for v in gap], 'print_gap_x': list(PLATE_GAPS[k])}
    return out


PLATE_SOLVE = ("T-2845 re-fit (tools/keith_loggia_built_read.py; report docs/RESEARCH/photo-match/"
               "keith_house_1808_prairie/keith-loggia-built-read.json): T-2763's level camera (verticals vertical, "
               "roll 0, square pixels; free: eye u, v and height, yaw, focal length and principal point) on the same "
               "27 coordinates, with the loggia's world points at the place the GLB now builds it, the first-floor "
               "plan's (T-2844's ruling): its front pedestals 0.6 m square at v 6.75-7.35 and 9.6-10.2, the pairs over "
               "their middles. RMS {rms:.2f} px, max {mx:.2f} px; {bound}. Eye {eye}, yaw {yaw:.3f}. T-2763's fit, "
               "which this replaces, put the loggia's controls at the old place (0.9 m pedestals at v 7.0-7.9 and "
               "9.5-10.4), RMS 4.94 px, and on the rebuilt GLB drew both pairs about 13 px south of the print's. "
               "Its text follows. ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help=f'write {REPORT.relative_to(ROOT)} and both cameras')
    args = ap.parse_args()
    # 1. the plate
    p, r, at_bound = pf.fit(R.plate_controls(BUILT), False)
    plate = R.plate_fit(BUILT)
    plate['pairs'] = pairs_on_plate(p, BUILT, PITCH)
    plate['pairs_at_the_old_pitch_0_45'] = pairs_on_plate(p, BUILT, 0.45)
    print(f"plate: RMS {plate['rms_px']} max {plate['max_px']} eye {plate['eye']} yaw {plate['yaw']} bound {at_bound}")
    print(f"  pair centres {plate['pair_centre_x']} ({plate['pair_centre_dx_px']} px from the print's)")
    for k, v in plate['pairs'].items():
        print(f"  {k}: {v}  (pitch 0.45: {plate['pairs_at_the_old_pitch_0_45'][k]['gap_x']})")
    # 2. the slide, the shafts at their built pitch
    R.SHAFT_OFF = PITCH / 2
    slide, cams = {}, {}
    for free, label in R.SLIDE_FITS:
        c, q = R.slide_fit(BUILT, free)
        slide[label] = q
        cams[tuple(free)] = c
        print(f"1965 {label:30s} RMS {q['rms_px']:5.2f} max {q['max_px']:5.1f} {q['params']} eye {q['eye_uv']} "
              f"heights {q['loggia_dy_px']}  shafts {q['loggia_dx_px']}")
    if args.write:
        cam = json.loads(PLATE_CAMERA.read_text())
        old = cam['solve']
        cam.update({'principal_px': [round(float(p[5]), 2), round(float(p[6]), 2)], 'focal_px': round(float(p[4]), 2),
                    'eye': [round(float(v), 3) for v in p[:3]], 'yaw_deg': round(float(p[3]), 3)})
        cam['solve'] = PLATE_SOLVE.format(rms=plate['rms_px'], mx=plate['max_px'],
                                          bound='no parameter at a bound' if not at_bound else f'at a bound: {at_bound}',
                                          eye=cam['eye'], yaw=cam['yaw_deg']) + old
        PLATE_CAMERA.write_text(json.dumps(cam, indent=2, ensure_ascii=False) + '\n')
        chosen = slide['nothing more free']
        cam65 = R.camera_file(cams[()], chosen, BUILT)
        cam65['solve'] = cam65['solve'].replace(
            'where the GLB still stands them 0.9 m wide at v 7.0-7.9 and 9.5-10.4, so this camera does not lean on '
            'the loggia the plan refuses',
            'where the GLB now builds them (T-2845), each pair\'s shafts 0.36 m apart; re-fitted by '
            'tools/keith_loggia_built_read.py on the rebuilt loggia').replace('T-2836 re-solve', 'T-2845 re-solve')
        lf.CAMERA.write_text(json.dumps(cam65, indent=2) + '\n')
        REPORT.write_text(json.dumps({
            '_doc': 'Written by tools/keith_loggia_built_read.py (T-2845): the 1888 plate and the 1965 slide re-fitted '
                    'on the GLB that builds the loggia at the first-floor plan\'s place. Read the tool\'s docstring.',
            'glb': str(lf.GLB.relative_to(ROOT)), 'glb_sha256': hashlib.sha256(lf.GLB.read_bytes()).hexdigest(),
            'built': {k: list(v) for k, v in BUILT.items()}, 'pitch_m': PITCH, 'shaft_r_m': SHAFT_R,
            'plate_refit': plate, 'slide_refits': slide, 'slide_camera_chosen': 'nothing more free'}, indent=1) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}, {PLATE_CAMERA.relative_to(ROOT)}, {lf.CAMERA.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
