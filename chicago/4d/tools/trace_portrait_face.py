#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""A face traced onto its portrait, beyond what the face axes can draw (T-3553).

Withdrawn for the Greys on 2026-11-13 (owner: "her jaw is ragged", "he has no chin and almost no
nose"): spot moves where one view disagreed with a face fitted from the other left lumps. Their
side views now go into the fit itself (tools/fit_portrait_face.py, a portrait record's
`fit_views`), and no trace file is written for them; the tool is kept for a later, smoothed use.

    python3 tools/trace_portrait_face.py DETECTIONS.json      add one pass to each person's trace
    python3 tools/trace_portrait_face.py --rebase PERSON      tie the trace to a refit, then run passes
    (tools/trace_portrait_profile.py adds side-view passes to the same trace, through profile_pass)

The owner, 2026-11-13, of the Greys' stand-in likenesses: "she needs a more serious match to
her features from the original photo, you need to trace it", and of both: "focus on their noses
a bit more they seem mis-traced". tools/fit_portrait_face.py fits MakeHuman's face axes to the
portrait's points; each axis moves a whole region one way, so a face whose cheekbones, chin and
nose differ from the body's in ways no axis draws is left a few millimetres off them (Sarah
Grey's cheekbones about 4 mm narrower than her picture's and her chin 4 mm wider, measured on a
render). The trace is the rest of the way: a smooth per-vertex displacement of the face, on top
of the fitted axes, that carries the points the face-landmark model finds on a render of the
fitted figure onto the points it finds on the portrait.

DETECTIONS.json is {"<person>": {"portrait": [[x, y] x 478], "model": [[x, y] x 478],
"pose": {"yaw_deg", "pitch_deg", "roll_deg"}, "view": optional name of another front picture of the
same stand-in traced instead of the portrait, such as a turnaround sheet's front view}}:
MediaPipe Face Landmarker (float16 v1, the same detector tools/face_landmark_correspondence.py
uses) run on the portrait and on a render of the person as the renderer draws them now
(tools/human_variation_lineup.html, keys=<person>, dress=1, turned by `pose`: the fit camera's
yaw, pitch and roll, or the turn near it at which the render's points lie best on the
portrait's; the trace already written is in that render). A pass:

  1. The render's points are laid on the portrait's by a similarity (rotation, scale, shift)
     over the points off the face's outline, and each point's miss is read in the portrait.
  2. Each miss is lifted into the head's own frame through the fit's camera. The face is
     symmetric, so a point and its mirror share one displacement (x mirrored): a point on the
     midline moves only up, down, in and out, and a pair's common sideways miss in a turned
     view is read as depth, held back hard by a ridge: from one turned picture a pixel of
     sideways miss is three of depth, so depth is left mostly to the fit and the reader.
  3. The displacements, at the skin vertices the landmark table ties each point to
     (data/humans/variation/mediapipe_hm08_landmarks.json; the outline ring by the render turn
     nearest the fit's), are spread over the face by a Gaussian average 9 mm wide that dies
     away 2 cm beyond the last point; the eyes' own points are held still, so the eyeballs,
     which ride the nearest skin, are not pulled out of shape. The brows' points are left out:
     the detector finds the brow hairs there, which the hair styles place, not the skin.
  4. A damped share (0.8) is added to the person's trace; no vertex is moved more than 16 mm
     in all (a side view lengthened Sarah Grey's nose and brought its bridge forward by about
     that much).

A record limits what is traced with its portrait record's `trace.points`: `all`, `inner` (no
outline ring), `nose` (the nose alone, the eyes held: a beard hides the jaw and mouth from
the detector on both pictures, and its hairs read as folds in the skin), or `nose_outline` (the
nose and the face's outline: on a bearded face the outline the detector finds is the beard's
on both pictures, so tracing it brings the jaw under the beard to the line that gives the
picture's beard outline). The trace is
written to data/humans/variation/traces/<person>.json in the kit's vertex order and units, with
the sha256 of the fit it was traced on; tools/human_variation_kit.py carries it into the
persons file and refuses one traced on another fit (re-run this after a refit). A reading,
regenerated only by this tool from fresh renders; never edit by hand. Reconstructed, like the
fit (L-human-variation-3412): it carries a stand-in's photograph's face, not the person's.
"""
import hashlib
import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fit_portrait_face as fpf  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
TRACES = ROOT / 'data/humans/variation/traces'
TABLE = ROOT / 'data/humans/variation/mediapipe_hm08_landmarks.json'
FACE_OVAL = {10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377,
             152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109}
# The eyes' own contours (MediaPipe's left and right eye rings and irises' lids).
EYES = {33, 7, 163, 144, 145, 153, 154, 155, 133, 246, 161, 160, 159, 158, 157, 173,
        263, 249, 390, 373, 374, 380, 381, 382, 362, 466, 388, 387, 386, 385, 384, 398}
# The brows' points are where the detector sees the brow HAIRS, which the hair styles place
# (human-hair-styles.js), not the skin: they are not traced.
# The nose, for a record that traces only it (`trace.points`: `nose`).
NOSE = {168, 6, 197, 195, 5, 4, 1, 19, 94, 2, 97, 98, 64, 48, 115, 220, 45, 51, 3, 196, 122, 193, 245, 128, 114,
        217, 198, 209, 49, 129, 326, 327, 294, 278, 344, 440, 275, 281, 248, 419, 351, 417, 465, 357, 343, 437,
        420, 429, 279, 358, 460, 99, 240, 75, 305, 290, 328, 59, 289, 60, 166, 79, 239, 238, 241, 242, 141, 125,
        44, 1, 274, 354, 370, 462, 250, 309, 392, 459, 458, 461}
BROWS = {70, 63, 105, 66, 107, 55, 65, 52, 53, 46, 300, 293, 334, 296, 336, 285, 295, 282, 283, 276}
UNIT = 1e-5          # metres, the kit's delta unit
SIGMA = 0.009        # the spread of a point's displacement over the skin, metres
FADE = 2.0           # in sigmas: beyond about this far from every point the trace dies away
DAMP = 0.8
RIDGE_XY, RIDGE_Z = 0.05, 2.0
CLIP = 0.016         # no vertex moves more than 16 mm in all


def similarity(a, b):
    ma, mb = a.mean(0), b.mean(0)
    A, B = a - ma, b - mb
    U, S, Vt = np.linalg.svd(A.T @ B)
    R = (U @ Vt).T
    s = S.sum() / (A ** 2).sum()
    return R, s, ma, mb


def trace_pass(person, det):
    portrait = json.loads((fpf.PORTRAITS / f'{person}.json').read_text())
    fit_path = fpf.FITS / f'{person}.json'
    fit_text = fit_path.read_text()
    fit = json.loads(fit_text)
    asset = portrait['base_body']
    cam = fit['fit']['camera']
    # The turn the render was made at: the fit's own camera, or the turn at which the render's
    # points lie best on the portrait's (a weak-perspective fit and the renderer's figure turn
    # differ by a few degrees: William Grey's 20.5 degrees reads as 16 on the figure).
    pose = det.get('pose') or {k: cam[k] for k in ('yaw_deg', 'pitch_deg', 'roll_deg')}
    R = fpf.rot(*(np.radians(pose[k]) for k in ('yaw_deg', 'pitch_deg', 'roll_deg')))
    scope = (portrait.get('trace') or {}).get('points', 'all')
    table = json.loads(TABLE.read_text())['bodies'][asset]
    points = {int(n[3:]): p['vertex'] for n, p in table['points'].items()}
    if scope in ('nose', 'nose_outline'):
        points = {i: v for i, v in points.items() if i in NOSE or i in EYES}
    if scope in ('all', 'nose_outline'):
        ring = min(table['outline'], key=lambda o: abs(o['render_yaw_deg'] - pose['yaw_deg']))
        points.update({int(n[4:]): p['vertex'] for n, p in ring['points'].items()})
    kidx = fpf.kit_index()
    rest = fpf.body_rest(asset)

    a = np.array(det['model'], float)[:468]
    b = np.array(det['portrait'], float)[:468]
    core = [i for i in range(468) if i not in FACE_OVAL]
    Ra, sa, ma, mb = similarity(a[core], b[core])
    A = (a - ma) @ Ra.T * sa + mb
    miss = b - A                                               # portrait pixels

    # Portrait pixels to the camera plane, metres: the same similarity, from the rest face's
    # points turned by the fit's camera (x right, y up) to the portrait's points (y down).
    used = sorted(i for i in points if points[i] in kidx and i not in BROWS)
    X = rest[[kidx[points[i]] for i in used]]
    Y = (X - X.mean(0)) @ R.T
    Rc, sc, _, _ = similarity(Y[:, :2] * np.array([1.0, -1.0]), b[used])
    to_cam = lambda e: (Rc.T @ e) / sc * np.array([1.0, -1.0])   # noqa: E731

    # A point and its mirror share one displacement: pair each used vertex with its mirror.
    pos = {i: rest[kidx[points[i]]] for i in used}
    P = R[:2]                                                   # camera-plane rows
    Mx = np.diag([-1.0, 1.0, 1.0])
    groups, seen = [], set()
    for i in used:
        if i in seen:
            continue
        q = pos[i] * np.array([-1.0, 1.0, 1.0])
        j = min((k for k in used if k not in seen and k != i), key=lambda k: np.linalg.norm(pos[k] - q), default=None)
        if abs(pos[i][0]) > 0.003 and j is not None and np.linalg.norm(pos[j] - q) < 0.004:
            groups.append((i, j)); seen.update((i, j))
        else:
            groups.append((i,)); seen.add(i)
    centres, moves, weights = [], [], []
    for g in groups:
        if any(k in EYES for k in g):
            for k in g:
                centres.append(pos[k]); moves.append(np.zeros(3)); weights.append(3.0)
            continue
        rows, rhs = [], []
        for n, k in enumerate(g):
            Pk = P if n == 0 else P @ Mx
            rows.append(Pk); rhs.append(to_cam(miss[k]))
        if len(g) == 1 and abs(pos[g[0]][0]) <= 0.003:          # on the midline: no sideways move
            rows.append(np.array([[1e3, 0, 0]])); rhs.append(np.zeros(1))
        Am = np.vstack(rows + [np.diag([RIDGE_XY, RIDGE_XY, RIDGE_Z])])
        bm = np.concatenate(rhs + [np.zeros(3)])
        d = np.linalg.lstsq(Am, bm, rcond=None)[0]
        for n, k in enumerate(g):
            centres.append(pos[k]); moves.append(d if n == 0 else Mx @ d); weights.append(1.0)
    C, D, Wt = np.array(centres), np.array(moves), np.array(weights)

    info = {'render_pose_deg': {k: round(float(pose[k]), 1) for k in ('yaw_deg', 'pitch_deg', 'roll_deg')},
            'miss_before_px': {'rms': round(float(np.sqrt((miss[used] ** 2).sum(1).mean())), 2),
                               'eye_span': round(float(np.linalg.norm(b[33] - b[263])), 1)}}
    if det.get('view'):
        info['front_view'] = det['view']
    add_to_trace(person, fit_text, fit, asset, rest, C, D, Wt, info, 'passes', scope)


def add_to_trace(person, fit_text, fit, asset, rest, C, D, Wt, info, counter, scope):
    """Spread displacements at centres C (rest frame, metres) over the skin near them and add a
    damped share to the person's trace; `counter` names the pass count to advance."""
    # Spread over the skin near the points.
    near = np.where(np.min(np.linalg.norm(rest[:, None, :] - C[None, :, :], axis=2), axis=1) < SIGMA * (FADE + 1.5))[0]
    K = np.exp(-np.sum((rest[near][:, None, :] - C[None, :, :]) ** 2, axis=2) / (2 * SIGMA ** 2)) * Wt
    field = (K @ D) / (K.sum(1) + np.exp(-FADE ** 2 / 2))[:, None] * DAMP

    out = TRACES / f'{person}.json'
    old = json.loads(out.read_text()) if out.exists() else None
    total = np.zeros_like(rest)
    if old:
        idx = np.array(old['vertices'], int)
        total[idx] = np.array(old['delta'], float).reshape(-1, 3) * UNIT
    total[near] += field
    mag = np.linalg.norm(total, axis=1)
    total *= np.minimum(1.0, CLIP / np.maximum(mag, 1e-12))[:, None]
    rec_info = dict(info)
    q = np.round(total / UNIT).astype(int)
    keep = np.where(np.abs(q).max(1) >= 2)[0]                  # 0.02 mm and up
    rec = {
        'format': 'chicago4d_human_face_trace_v1',
        'ticket': 'T-3553',
        'person_id': person,
        'generated_by': 'tools/trace_portrait_face.py',
        '_doc': 'A per-vertex displacement of the face beyond the fitted axes, in the kit vertex order (vertices) and the kit delta unit (unit_m), carried by tools/human_variation_kit.py into the persons file. A reading, regenerated only by the tool from fresh renders; never edit by hand.',
        'grade': fit['grade'],
        'liberty': 'L-human-variation-3412',
        'body': asset,
        'points': scope,
        'render_pose_deg': (old or {}).get('render_pose_deg'),
        'fit_sha256': hashlib.sha256(fit_text.encode()).hexdigest(),
        'passes': (old or {}).get('passes', 0),
        'miss_before_px': (old or {}).get('miss_before_px'),
        'profile_passes': (old or {}).get('profile_passes', 0),
        'profile_miss_mm': (old or {}).get('profile_miss_mm'),
        'max_mm': round(float(np.linalg.norm(q[keep] * UNIT, axis=1).max() * 1000), 2) if len(keep) else 0.0,
        'unit_m': UNIT,
        'vertices': [int(i) for i in keep],
        'delta': [int(v) for v in q[keep].ravel()],
    }
    for k in ('rebased', 'front_view'):
        if (old or {}).get(k) and k not in info:
            rec[k] = old[k]
    rec[counter] = rec[counter] + 1
    rec.update(rec_info)
    if not rec['profile_passes']:
        del rec['profile_passes'], rec['profile_miss_mm']
    TRACES.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, separators=(',', ':')).replace(',"vertices"', ',\n"vertices"').replace(',"delta"', ',\n"delta"') + '\n')
    print(f"{person}: {counter} {rec[counter]}, {json.dumps(rec_info)}, {len(keep)} vertices, max {rec['max_mm']} mm")


def profile_pass(person, d):
    """One pass from a side view: `d` holds the skin vertices on the render's silhouette (kit
    order) and each one's move, metres in the rest frame, onto the picture's silhouette, as
    tools/trace_portrait_profile.py reads them. A side view sees depth and height, not
    sideways: each move is shared with the vertex's mirror; the eyes are held still."""
    portrait = json.loads((fpf.PORTRAITS / f'{person}.json').read_text())
    fit_text = (fpf.FITS / f'{person}.json').read_text()
    fit = json.loads(fit_text)
    asset = portrait['base_body']
    rest = fpf.body_rest(asset)
    kidx = fpf.kit_index()
    table = json.loads(TABLE.read_text())['bodies'][asset]
    eyes = [kidx[p['vertex']] for n, p in table['points'].items() if int(n[3:]) in EYES and p['vertex'] in kidx]
    V = np.array(d['vertices'], int)
    M = np.array(d['moves'], float).reshape(-1, 3) * np.array([0.0, 1.0, 1.0])
    mirror = rest[V] * np.array([-1.0, 1.0, 1.0])
    C = np.vstack([rest[V], mirror, rest[eyes]])
    D = np.vstack([M, M, np.zeros((len(eyes), 3))])
    Wt = np.concatenate([np.ones(len(V)), np.ones(len(V)), np.full(len(eyes), 3.0)])
    info = {'profile_miss_mm': d.get('miss_mm')}
    add_to_trace(person, fit_text, fit, asset, rest, C, D, Wt, info, 'profile_passes',
                 (portrait.get('trace') or {}).get('points', 'all'))


def rebase(person):
    """After a refit, tie the person's trace to the new fit: the trace is a correction on top
    of the fitted face, so it stays roughly right; fresh front and side passes then correct
    what the refit moved."""
    out = TRACES / f'{person}.json'
    rec = json.loads(out.read_text())
    rec['fit_sha256'] = hashlib.sha256((fpf.FITS / f'{person}.json').read_text().encode()).hexdigest()
    rec['rebased'] = rec.get('rebased', 0) + 1
    out.write_text(json.dumps(rec, separators=(',', ':')).replace(',"vertices"', ',\n"vertices"').replace(',"delta"', ',\n"delta"') + '\n')
    print(f'{person}: trace tied to the refit (rebased {rec["rebased"]})')


def main():
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == '--rebase':
        rebase(args[1])
        return
    if len(args) == 2 and args[0] == '--profile':
        for person, d in json.loads(pathlib.Path(args[1]).read_text()).items():
            profile_pass(person, d)
        return
    if len(args) != 1:
        sys.exit(__doc__)
    det = json.loads(pathlib.Path(args[0]).read_text())
    for person, d in det.items():
        trace_pass(person, d)


if __name__ == '__main__':
    main()
