"""T-2879: read Glessner's court along S on HABS sheet 2 (plan) and sheet 4 (section A-A).

Run from chicago/4d:  python3 docs/RESEARCH/glessner-court-ruling-T-2879/read_court.py
Prints every reading the README quotes. Needs Pillow and numpy.

Sheet 2: building frame from T-2218's plan-controls.json (NE corner x2145/y4988,
37.25 px/ft along W, 37.46 px/ft along S, north down the sheet).
Sheet 4: T-2228's section controls (north wall x1165, 100.6 px/ft along S).
"""
import json, math, pathlib
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PUB = ROOT.parent / 'prairie_1904_v1' / 'research' / 'public'

ctl = json.loads((ROOT / 'docs/RESEARCH/glessner-courtyard-steps-T-2218/plan-controls.json').read_text())
NE_x, NE_y = ctl['control_NE']
PX_W = (ctl['control_NW'][0] - NE_x) / ctl['controls_ft'][0]
PX_S = (NE_y - ctl['control_SE'][1]) / ctl['controls_ft'][1]
def plan_S(y): return (NE_y - y) / PX_S
def plan_W(x): return (x - NE_x) / PX_W

sec = json.loads((ROOT / 'docs/RESEARCH/glessner-final-comparison-T-2228/section-controls.json').read_text())
N_WALL, PX_SEC = sec['north_wall_x'], sec['horizontal_px_ft']
def sec_S(x): return (x - N_WALL) / PX_SEC

def ink(path, thresh):
    return np.asarray(Image.open(path).convert('L')) < thresh

def peaks(profile, offset, floor, gap=4):
    """Ink-weighted centres of runs of `profile` above `floor`."""
    out, run = [], []
    for i, v in enumerate(profile):
        if v > floor: run.append((i + offset, float(v)))
        elif run and i + offset - run[-1][0] > gap:
            out.append(sum(p * w for p, w in run) / sum(w for _, w in run)); run = []
    if run: out.append(sum(p * w for p, w in run) / sum(w for _, w in run))
    return out

print('== sheet 2: the courtyard N-S chain (printed 47\'-2" = 12\'-8" + 10\'-0" + 12\'-0" + 12\'-6")')
s2 = ink(PUB / 'glessner-habs-sheet-2.tif', 160)
print(f'   scale {PX_W:.2f} px/ft (W), {PX_S:.2f} px/ft (S)')
# the chain's extension lines stand at about W46.5-50.8, left of the dimension line
band = s2[:, 3860:4020].sum(1)
def strongest(y0, y1):
    seg = band[y0:y1]; i = int(seg.argmax())
    lo, hi = max(0, i - 2), i + 3
    w = seg[lo:hi].astype(float)
    return y0 + (np.arange(lo, hi) * w).sum() / w.sum()
ticks = [strongest(2660, 2720), strongest(3050, 3120), strongest(3480, 3540)]
# the chain's north end is the range's court face. Its wall line is read either side
# of the chain's own text: beside the bow (W38-41.7) and just west of the A-A cut
# (W55.2-60). West of the dining bay the face steps north (T-1732's note), so it is
# not read there.
def face(x0, x1):
    prof = s2[3900:3995, x0:x1].sum(1); i = int(prof.argmax())
    w = prof[max(0, i - 2):i + 3].astype(float)
    return 3900 + (np.arange(max(0, i - 2), i + 3) * w).sum() / w.sum()
faces = [face(3560, 3700), face(4200, 4380)]
print('   court face beside the bow S%.2f, west of the cut S%.2f' % tuple(plan_S(f) for f in faces))
ticks.append(sum(faces) / 2)
printed = [74.0, 74.0 - 12 - 8/12, 74.0 - 22 - 8/12, 74.0 - 34 - 8/12, 74.0 - 47 - 2/12]
drawn = [plan_S(2213)] + [plan_S(t) for t in ticks]
print('   tick rows', [round(float(t), 1) for t in ticks])
for p, d in zip(printed, drawn):
    print(f'   printed S {p:6.2f}   drawn S {d:6.2f}   drawn-printed {d - p:+.2f}')

print('== sheet 2: the stair tower drum (outer face) ')
# outer arc: the westernmost ink of the drum's outer face, rows through the newel
cx_n, cy_n = 3155, 2883          # the newel's dot (UP/DN winder centre)
rows = range(cy_n - 120, cy_n + 121, 20)
west = []
for y in rows:
    xs = np.nonzero(s2[y, 3250:3420])[0]
    if len(xs): west.append((y, 3250 + xs.max()))
cw, cs = plan_W(cx_n), plan_S(cy_n)
rs = [math.hypot(plan_W(x) - cw, plan_S(y) - cs) for y, x in west]
print(f'   newel W{cw:.2f} S{cs:.2f}; outer-face radius about the newel {np.median(rs):.2f} ft '
      f'(range {min(rs):.2f}-{max(rs):.2f})')
r, cW, face = 5.25, 27.3, 26.5
half = math.sqrt(r * r - (cW - face) ** 2)
print(f'   record: r{r} at W{cW}, S56.1 meets the W{face} face at S{56.1 - half:.2f}-{56.1 + half:.2f}')

print('== sheet 4: positions along S at the section scale (S0 = north wall x1165)')
s4 = ink(PUB / 'glessner-habs-sheet-4.tif', 128)
def vline(x0, x1, y0, y1, floor):
    prof = s4[y0:y1, x0:x1].sum(0)
    return peaks(prof, x0, floor * (y1 - y0))
reads = {
    'north range court face (cut), rows 3000-3600': vline(3700, 3900, 3000, 3600, .5),
    'bow, south flank, rows 3600-4300': vline(4950, 5150, 3600, 4300, .5),
    'terminal post, north edge, rows 5500-5800': vline(5650, 5780, 5500, 5800, .5),
    'terminal post, south edge, rows 5450-5800': vline(5800, 5950, 5450, 5800, .2),
    'stair tower drum, rows 3000-4500': vline(6200, 6400, 3000, 4500, .5) + vline(7350, 7550, 3000, 4500, .5),
}
for k, xs in reads.items():
    print(f'   {k}: ' + ', '.join(f'x{x:.0f} = S{sec_S(x):.2f}' for x in xs))
