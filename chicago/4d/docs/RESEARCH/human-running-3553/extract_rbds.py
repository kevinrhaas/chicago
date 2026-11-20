#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3553: the running reference for human-gait.js, from the public running dataset RBDS.

Fukuchi RK, Fukuchi CA, Duarte M (2017). A public data set of running biomechanics and the effects
of running speed on lower extremity kinematics and kinetics. PeerJ 5:e3298. Data: figshare
doi:10.6084/m9.figshare.4543435 (v5): treadmill running at 2.5, 3.5 and 4.5 m/s.

    python3 extract_rbds.py fetch <dir>    # download the processed files, and stream every
                                           # running marker file (about 340 MB) to its stride
                                           # time and pelvis excursion, keeping only those
    python3 extract_rbds.py build <dir>    # write data/humans/gait/normative_running.json

What is read:
  - *processed.txt (Visual3D, per-runner ensemble mean over the cycle from the reference foot's
    contact, 101 points): hip, knee and ankle angles, Z = the sagittal component (+ flexion, +
    dorsiflexion); left and right legs each a sample. The vertical ground reaction force (the Y
    component, present only while the foot is down) gives toe-off as the last sample above 5 % of
    its peak; a runner whose force runs the whole cycle (a processing fault) is left out of it.
  - *runT??markers.txt (150 Hz): the stride time as the autocorrelation peak of the right heel
    marker's height between 0.45 and 1.0 s; the stride length is the belt speed times it; the
    pelvis's vertical excursion is the median over strides of the range of the four pelvis
    markers' mean height.
"""
import glob
import json
import math
import re
import statistics as st
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARTICLE = 'https://api.figshare.com/v2/articles/4543435'
SPEEDS = ('25', '35', '45')


def fetch(d):
    d.mkdir(parents=True, exist_ok=True)
    meta = json.loads(urllib.request.urlopen(ARTICLE).read())
    (d / 'meta.json').write_text(json.dumps(meta))
    out = (d / 'strides.jsonl').open('w')
    for f in meta['files']:
        n = f['name']
        if n.endswith('processed.txt') or n == 'RBDSinfo.txt':
            (d / n).write_bytes(urllib.request.urlopen(f['download_url']).read())
        elif re.match(r'RBDS\d+runT\d\dmarkers\.txt$', n):
            tmp = d / n
            tmp.write_bytes(urllib.request.urlopen(f['download_url']).read())
            out.write(json.dumps(stride(tmp)) + '\n')
            tmp.unlink()


def rows_of(path):
    L = [l.rstrip('\r\n').split('\t') for l in open(path)]
    h = L[0]
    num = lambda x: float(x) if x.strip() and x.lower() != 'nan' else float('nan')
    return h, [[num(x) for x in r] for r in L[1:] if len(r) == len(h)]


def stride(path):
    h, rows = rows_of(path)
    t = [r[0] for r in rows]
    dt = (t[-1] - t[0]) / (len(t) - 1)
    col = lambda n: [r[h.index(n)] for r in rows]
    hy = col('R.Heel.BottomY')
    ok = [x for x in hy if x == x]
    m = sum(ok) / len(ok)
    hy = [x - m if x == x else 0.0 for x in hy]
    best = max(range(int(0.45 / dt), int(1.0 / dt)), key=lambda lag: sum(hy[i] * hy[i + lag] for i in range(0, len(hy) - lag, 2)))
    pel = [sum(v) / 4 for v in zip(col('R.ASISY'), col('L.ASISY'), col('R.PSISY'), col('L.PSISY'))]
    rng = sorted(max(s) - min(s) for s in ([x for x in pel[i:i + best] if x == x] for i in range(0, len(pel) - best, best)) if s)
    return {'file': path.name, 'stride_s': round(best * dt, 4), 'pelvis_range_mm': round(rng[len(rng) // 2], 1)}


def build(d):
    tables, events = {}, {}
    files = sorted(glob.glob(str(d / 'RBDS*processed.txt')))
    for sp in SPEEDS:
        acc = {'hip': [], 'knee': [], 'ankle': []}
        toe, runners = [], 0
        for f in files:
            h, rows = rows_of(f)
            if f'RhipAngZ{sp}' not in h: continue
            runners += 1
            for side in 'RL':
                for k in acc:
                    c = [r[h.index(f'{side}{k}AngZ{sp}')] for r in rows]
                    if all(x == x for x in c): acc[k].append(c)
                g = [r[h.index(f'{side}grfY{sp}')] for r in rows]
                g = [0.0 if x != x else x for x in g]
                top = max(g)
                last = max(j for j, x in enumerate(g) if x > 0.05 * top)
                if last < 60: toe.append(last)
        v = int(sp) / 10
        for k, c in acc.items():
            tables.setdefault(k, {})[sp] = {
                'values': [round(sum(x[j] for x in c) / len(c), 1) for j in range(0, 101, 5)],
                'sd': [round(st.pstdev([x[j] for x in c]), 1) for j in range(0, 101, 5)],
                'n_legs': len(c)}
        events[sp] = {'speed_m_s': v, 'toe_off_pct_median': st.median(toe), 'n_legs': len(toe), 'n_runners': runners}
    info = {}
    hdr, *rows = [l.rstrip('\r\n').split('\t') for l in open(d / 'RBDSinfo.txt')]
    for r in rows: info[int(r[0])] = float(r[hdr.index('Height')]) / 100
    sp_rows = {}
    for line in open(d / 'strides.jsonl'):
        r = json.loads(line)
        sp = re.search(r'runT(\d\d)', r['file']).group(1)
        if 0.55 < r['stride_s'] < 0.95: sp_rows.setdefault(sp, []).append(r)
    spatio = {}
    for sp, rs in sorted(sp_rows.items()):
        v = int(sp) / 10
        T = st.median(r['stride_s'] for r in rs)
        rel = [v * r['stride_s'] / info[int(r['file'][4:7])] for r in rs if int(r['file'][4:7]) in info]
        spatio[sp] = {'speed_m_s': v, 'stride_time_s': round(T, 3), 'cadence_steps_min': round(120 / T, 1), 'stride_m': round(v * T, 2),
                      'stride_over_height': round(st.median(rel), 3), 'pelvis_vertical_range_mm': st.median(r['pelvis_range_mm'] for r in rs),
                      'n_trials': len(rs), 'n_with_height': len(rel)}
    doc = {
        'schema': 'normative_running/1',
        'title': 'Normative human running reference for the procedural gait layer (human-gait.js RUN_CURVES)',
        'cycle_convention': 'Percent of the running cycle, 0 = initial contact of the reference foot, 100 = its next contact; 21 samples at 0,5,...,100. Left and right legs are each a sample.',
        'provenance_note': 'Computed here from the downloaded open dataset by docs/RESEARCH/human-running-3553/extract_rbds.py (method in its header). Treadmill running by recreational and competitive runners in running shoes. Stride over stature uses the runners RBDSinfo.txt lists (28, aged 22-51, 27 men).',
        'sources': [{'id': 'fukuchi2017_rbds', 'citation': 'Fukuchi RK, Fukuchi CA, Duarte M (2017). A public data set of running biomechanics and the effects of running speed on lower extremity kinematics and kinetics. PeerJ 5:e3298. Data: figshare doi:10.6084/m9.figshare.4543435 (v5).',
                     'url': 'https://doi.org/10.7717/peerj.3298', 'data_url': 'https://doi.org/10.6084/m9.figshare.4543435',
                     'what': 'USED. *processed.txt angles and vertical ground reaction force at 2.5, 3.5 and 4.5 m/s; *runT??markers.txt for stride time and pelvis excursion; RBDSinfo.txt for stature.'}],
        'cycle_tables': {f'{k}_flexion_deg' if k != 'ankle' else 'ankle_dorsiflexion_deg': {
            'unit': 'deg, + flexion' if k != 'ankle' else 'deg, + dorsiflexion', 'ref': 'fukuchi2017_rbds', 'basis': 'dataset mean', 'by_speed': t} for k, t in tables.items()},
        'events': events,
        'spatiotemporal': spatio,
        'beyond_measured': 'The dataset stops at 4.5 m/s. human-gait.js carries the trend of each measured number past it (a sprint at 5-6 m/s); that extrapolation is reconstruction, not evidence (liberty L-human-gait-3472).',
    }
    out = ROOT / 'data/humans/gait/normative_running.json'
    out.write_text(json.dumps(doc, indent=1) + '\n')
    print(f'wrote {out.relative_to(ROOT)}')
    for sp in SPEEDS:
        print(sp, events[sp], spatio.get(sp))


if __name__ == '__main__':
    {'fetch': fetch, 'build': build}[sys.argv[1]](Path(sys.argv[2]))
