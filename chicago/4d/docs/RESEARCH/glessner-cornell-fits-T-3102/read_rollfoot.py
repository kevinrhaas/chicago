#!/usr/bin/env python3
"""T-3102: the stable's alley-end roll foot and eave, read through every camera of the valley.

Runs T-3080's read_slope.py unchanged on the GLB of the tree it is run in, with the Cornell
cameras of readings.json's valley (read_fits.py) added to T-2758's, and reports the roll foot
and eave the way T-3096's acceptance does (read_rebuild.py: roll foot = 0.09 m less the plane
top's offset, T-3095 section 1). It records the GLB's sha256, so a reading is tied to the
geometry it was read on.

Needs the gitignored GLB: python3 tools/recover_glessner_v4.py --materialize

    python3 docs/RESEARCH/glessner-cornell-fits-T-3102/read_rollfoot.py    writes rollfoot-readings.json
"""
from pathlib import Path
import hashlib, json, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'docs/RESEARCH/glessner-roof-slope-camera-T-3080'))
import read_slope as rs  # noqa: E402

ROLL_FOOT_M = 0.09   # as read_rebuild.py (T-3096)
VIEW = 'cornell-northwest-west-windows'


def main():
    valley = json.loads((HERE / 'readings.json').read_text())['valley']
    fits = json.loads(rs.FITS.read_text())
    names = ['roof_pitched', 'roof_level']
    for k, v in valley.items():
        fits['cornell'][f'tilt_{k}'] = {'camera': v['camera'], 'what': f'T-3102 valley, tilt {k}', 'rms_px': v['controls_rms_px']}
        names.append(f'tilt_{k}')
    scratch = ROOT / 'data/comparisons/glessner/.t3102-scratch-fits.json'
    scratch.write_text(json.dumps(fits))
    out = HERE / '.scratch'
    out.mkdir(exist_ok=True)
    try:
        rs.FITS, rs.HERE = scratch, out
        rs.CAMERAS = {VIEW: ('cornell', names)}
        rs.main()
        rows = json.loads((out / 'readings.json').read_text())['views'][VIEW]
    finally:
        scratch.unlink()
        for f in out.iterdir():
            f.unlink()
        out.rmdir()
    glb = rs.rm.GLB
    report = {
        'ticket': 'T-3102',
        'glb': str(glb.relative_to(ROOT)), 'glb_sha256': hashlib.sha256(glb.read_bytes()).hexdigest(),
        'how': 'read_slope.py (T-3080) unchanged; roll foot and eave as read_rebuild.py (T-3096). Positive: the print\'s stands higher.',
        'cameras': {r['camera']: {'controls_rms_px': r['rms_px_on_measured_controls'], 'print_courses': r['print_courses'],
                                  'print_over_model_roll_foot_m': [round(ROLL_FOOT_M - c['ridge_below_model_top_m'], 2) for c in r['columns']],
                                  'print_eave_over_model_eave_m': [round(-c['eave_below_model_foot_m'], 2) for c in r['columns']]}
                    for r in rows},
    }
    (HERE / 'rollfoot-readings.json').write_text(json.dumps(report, indent=1) + '\n')
    for k, v in report['cameras'].items():
        print(f"{k:14s} roll foot {v['print_over_model_roll_foot_m']}  eave {v['print_eave_over_model_eave_m']}  courses {v['print_courses']}")


if __name__ == '__main__':
    main()
