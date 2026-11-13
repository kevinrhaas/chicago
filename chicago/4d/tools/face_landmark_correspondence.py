#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Which skin vertex of a body each MediaPipe face landmark falls on (T-3553).

    python3 tools/face_landmark_correspondence.py DETECTIONS.json      write the table

A portrait record may mark a face with MediaPipe Face Landmarker's points (`mp_<index>`),
hundreds where a reader marks about fifteen, so that a face fit is held by the whole face and
not by its prior (T-3553, the owner: "their faces must match exactly"). The fit has to know
which vertex of the body each point is, AS THE SAME DETECTOR SEES IT, or the fit spends its
axes undoing the detector's own habits (a first try that laid MediaPipe's canonical face on
base.obj by geometry gave fits with brows, cheeks and nose driven to their limits).

So the table is read off the bodies themselves. Each body's own rest face is rendered bare
(tools/human_variation_lineup.html, key `base`: no variation, no hair or hat, dressed skin) at
five turns (yaw -25, -12, 0, 12, 25 degrees), and MediaPipe Face Landmarker (float16 v1) is run
on each render; DETECTIONS.json is {"<asset>_<yaw>.png": [[x, y] x 478], ...}. For each render
a weak-perspective camera (the fit's own) is solved from the named landmarks
tools/fit_portrait_face.py finds from the mesh's geometry, the body's head vertices are
projected through it (a vertex hidden behind nearer skin within 4 px is not a candidate), and
each MediaPipe point is given the vertex whose projections lie nearest the detected point over
all five renders. The face's outline ring (FACE_OVAL) is a silhouette, a different skin point
in every pose, so it is kept per render (`outline`, by the camera yaw solved there, as
`mpo_<index>`); a portrait record using it names the turn it was matched to (`outline_yaw_deg`). `px` is the root-mean-square miss over the renders, in
pixels at about 3.5 px per mm; a point that misses by more than 15 px is left out.

    data/humans/variation/mediapipe_hm08_landmarks.json
"""
import json
import pathlib
import re
import sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fit_portrait_face as fpf  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/humans/variation/mediapipe_hm08_landmarks.json'
FACE_OVAL = {10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377,
             152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109}
NAMED = {'eye_outer_r': [33], 'eye_inner_r': [133], 'eye_inner_l': [362], 'eye_outer_l': [263],
         'nasion': [168], 'nose_tip': [1], 'subnasale': [2], 'stomion': [13, 14], 'menton': [152]}


def table_for(asset, renders):
    V, groups = fpf.read_base()
    lm = fpf.landmarks()
    kidx = fpf.kit_index()
    rest = fpf.body_rest(asset)
    body = np.array(sorted(groups['body']))
    head = np.array([v for v in body if V[v, 1] > 6.0 and V[v, 2] > 0.5 and v in kidx])
    H = rest[[kidx[v] for v in head]]
    named = np.array([rest[kidx[lm[n]]] for n in NAMED])
    centre = H.mean(0)

    def project(X, cam):
        yaw, pitch, roll, s, tx, ty = cam
        Y = (X - centre) @ fpf.rot(yaw, pitch, roll).T
        return np.stack([tx + s * Y[:, 0], ty - s * Y[:, 1]], 1), Y[:, 2]

    cost = np.zeros((468, len(head)))
    seen = np.zeros((468, len(head)))
    outline = []
    for det, yaw in renders:
        D = np.array(det)
        obs = np.array([D[ix].mean(0) for ix in NAMED.values()])
        s0 = np.linalg.norm(obs[3] - obs[0]) / np.linalg.norm(named[3] - named[0])
        best = None
        for y0 in (np.radians(yaw), -np.radians(yaw)):
            r = least_squares(lambda c: (project(named, c)[0] - obs).ravel(), [y0, 0, 0, s0, *obs.mean(0)])
            if best is None or r.cost < best.cost:
                best = r
        P, depth = project(H, best.x)
        # Visible: no nearer vertex (by 4 mm) projects within 4 px.
        vis = np.ones(len(head), bool)
        for k in range(len(head)):
            near = np.abs(P - P[k]).max(1) < 4
            if (depth[near] > depth[k] + 0.004).any():
                vis[k] = False
        # The outline ring belongs to this turn alone: each of its points on the visible vertex
        # nearest it in this render (a silhouette point of a face turned this far).
        ring = {}
        for i in sorted(FACE_OVAL):
            d2 = np.where(vis, ((P - D[i]) ** 2).sum(1), np.inf)
            j = int(d2.argmin())
            if np.sqrt(d2[j]) <= 15:
                ring[f'mpo_{i}'] = {'vertex': int(head[j]), 'px': round(float(np.sqrt(d2[j])), 2)}
        outline.append({'render_yaw_deg': yaw, 'solved_yaw_deg': round(float(np.degrees(best.x[0])), 1), 'points': ring})
        for i in range(468):
            if i in FACE_OVAL:
                continue
            d2 = ((P - D[i]) ** 2).sum(1)
            cost[i] += np.where(vis, d2, 0)
            seen[i] += vis
    out = {}
    n = len(renders)
    for i in range(468):
        if i in FACE_OVAL:
            continue
        ok = seen[i] >= n - 1          # seen in all renders but at most one
        if not ok.any():
            continue
        mean = np.where(ok, cost[i] / np.maximum(seen[i], 1), np.inf)
        j = int(mean.argmin())
        if np.sqrt(mean[j]) > 15:
            continue
        out[f'mp_{i}'] = {'vertex': int(head[j]), 'px': round(float(np.sqrt(mean[j])), 2)}
    return out, outline


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    det = json.loads(pathlib.Path(sys.argv[1]).read_text())
    byasset = {}
    for name, pts in det.items():
        m = re.match(r'(.+)_(-?\d+)\.png$', pathlib.Path(name).name)
        byasset.setdefault(m.group(1), []).append((pts, int(m.group(2))))
    bodies = {}
    for a, r in sorted(byasset.items()):
        pts, outline = table_for(a, sorted(r, key=lambda x: x[1]))
        bodies[a] = {'renders': len(r), 'points': pts, 'outline': outline}
    OUT.write_text(json.dumps({
        'format': 'chicago4d_mediapipe_body_landmarks_v1', 'ticket': 'T-3553',
        'generated_by': 'tools/face_landmark_correspondence.py',
        '_doc': 'Per body: MediaPipe Face Landmarker point -> the base.obj skin vertex (source index) it falls on, read off renders of the body\'s own bare rest face at five turns (see the tool). `px` is the mean miss over those renders. The face outline ring is left out. A reading, regenerated only by the tool from fresh renders; never edit by hand.',
        'detector': 'MediaPipe Face Landmarker, face_landmarker.task float16 v1 (Apache-2.0)',
        'bodies': bodies}, indent=1) + '\n')
    for a, b in bodies.items():
        px = [p['px'] for p in b['points'].values()]
        print(f'{a}: {len(px)} points, median miss {np.median(px):.2f} px, worst {max(px):.2f}')


if __name__ == '__main__':
    main()
