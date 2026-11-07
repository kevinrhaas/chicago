# SPDX-License-Identifier: GPL-3.0-or-later
"""The wardrobe kit (T-3409): loose garments for any portable human, from a recipe.

T-3398 dressed Hans for the brougham's box; this is that tool made general, so every
person is dressed the same way and every garment carries its own provenance. A
recipe (data/humans/wardrobes/<id>.json) names a body master, the clip it is
dressed in, the vehicle or ground it sits on, and a list of garments. The kinds:

  shell        a garment cut from one of the body's own garment meshes, stood off it
               by the cloth's loft (more at a collar, eased at the cuff), smoothed so
               the anatomy beneath no longer shows, held clear of the body;
  drape_hem    a cloth hung from a shell's lowest edge (a coat skirt) and DROPPED
               under gravity by position-based dynamics onto the body and the
               vehicle, so its folds are where the cloth had to go;
  drape_collar a cloth hung from round a shell's collar foot (a shoulder cape);
  hat          a hat fitted to the head's own cross-section: a crown profile, a brim
               that curls at the sides or droops fore and aft, and a band;
  buttons      discs down a shell's front;
  gloves       gloves cut from the body's own hands, a gauntlet riding over the cuff.

Garments are skinned to the body's own skeleton (weights copied from the garment
they were cut from, or taken from the nearest body points), unposed through the
dressed pose to the bind pose. Hanging cloth may also take SPRING TAILS: a few
extra bones, parented to the body's bones, that a renderer swings behind the body
as it moves (renderers/web/js/driver-livery.js), so a cape or a skirt that hangs
free sways with the carriage. At rest a tail moves exactly with its parent, so the
draped shape is unchanged.

Every garment declares its grade and either the sources it rests on (with their
scope) or the liberty that records it; the kit refuses a garment with neither.

The producer is tools/human_wardrobe.py.
"""
from __future__ import annotations

import base64, hashlib, json, math, re, sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / 'tools'))
import human_working_driver_1904 as H  # noqa: E402  (load, accessor, matrices)

SCHEMA = 'chicago4d_wardrobe_v1'
GRADES = ('attested', 'inferred', 'reconstructed')


def sha(b): return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- the dressed body
def posed_locals(doc, buf, clip):
    """Node transforms at the first key of a constant (STEP) clip."""
    local = {i: {k: np.array(n.get(k, d), float) for k, d in [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])]}
             for i, n in enumerate(doc['nodes'])}
    anim = next(a for a in doc['animations'] if a['name'] == clip)
    for c in anim['channels']:
        s = anim['samplers'][c['sampler']]
        if s.get('interpolation') != 'STEP': raise SystemExit(f'wardrobe: clip {clip} is not a held pose')
        out = H.accessor(doc, buf, s['output'])
        if np.max(np.abs(out - out[0])) != 0: raise SystemExit(f'wardrobe: clip {clip} moves; dress in a held pose')
        local[c['target']['node']][c['target']['path']] = out[0].astype(float)
    return local


def dressed(body, asset_id, clip):
    """The body master posed in `clip`: each mesh's posed points, faces and skin, the
    joints' pose matrices and inverse binds, and the bones' posed heads."""
    doc, buf, body_sha = H.load(APP / body)
    glob, _ = H.matrices(doc, posed_locals(doc, buf, clip))
    skin = doc['skins'][0]
    ibm = H.accessor(doc, buf, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    joint_m = np.stack([glob[i] for i in skin['joints']]) @ ibm
    joints = [doc['nodes'][i]['name'] for i in skin['joints']]
    meshes = {}
    for node in doc['nodes']:
        if 'mesh' not in node: continue
        prim = doc['meshes'][node['mesh']]['primitives'][0]
        a = prim['attributes']
        v = H.accessor(doc, buf, a['POSITION'])
        j = H.accessor(doc, buf, a['JOINTS_0']).astype(int); w = H.accessor(doc, buf, a['WEIGHTS_0']).astype(float)
        m = np.einsum('vn,vnij->vij', w, joint_m[j])
        posed = np.einsum('vij,vj->vi', m, np.c_[v, np.ones(len(v))])[:, :3]
        ix = H.accessor(doc, buf, prim['indices']).astype(int).reshape(-1, 3)
        key = node['name'].split(f'{asset_id}_')[-1].rsplit('_lod', 1)[0]
        meshes[key] = dict(posed=posed, faces=ix, joints=j, weights=w)
    bones = {doc['nodes'][i]['name']: glob[i][:3, 3] for i in skin['joints']}
    return dict(sha=body_sha, joints=joints, joint_m=joint_m, ibm=ibm, meshes=meshes, bones=bones, body_joints=len(joints))


# ---------------------------------------------------------------- mesh helpers
def weld(P, F):
    _, idx, inv = np.unique(np.round(P * 1e5).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    inv = inv.ravel()
    return P[idx], inv[F], idx, inv


def vertex_normals(P, F):
    n = np.zeros_like(P)
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    for k in range(3): np.add.at(n, F[:, k], fn)
    return n / (np.linalg.norm(n, axis=1)[:, None] + 1e-12)


def edges(F):
    e = np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]
    return np.unique(np.sort(e, axis=1), axis=0)


def laplacian(P, E, n):
    acc = np.zeros_like(P); cnt = np.zeros(n)
    np.add.at(acc, E[:, 0], P[E[:, 1]]); np.add.at(acc, E[:, 1], P[E[:, 0]])
    np.add.at(cnt, E[:, 0], 1); np.add.at(cnt, E[:, 1], 1)
    return acc / np.maximum(cnt, 1)[:, None] - P


def boundary_vertices(G):
    e = np.sort(np.r_[G[:, [0, 1]], G[:, [1, 2]], G[:, [2, 0]]], axis=1)
    u, c = np.unique(e, axis=0, return_counts=True)
    return np.unique(u[c == 1].ravel())


def boundary_loops(G):
    e = np.sort(np.r_[G[:, [0, 1]], G[:, [1, 2]], G[:, [2, 0]]], axis=1)
    u, c = np.unique(e, axis=0, return_counts=True)
    adj = {}
    for a, b in u[c == 1]: adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    loops, seen = [], set()
    for s in adj:
        if s in seen: continue
        loop = [s]; seen.add(s); prev, cur = None, s
        while True:
            nxt = [v for v in adj[cur] if v != prev and v not in seen]
            if not nxt: break
            prev, cur = cur, nxt[0]; loop.append(cur); seen.add(cur)
        loops.append(loop)
    return loops


def orient_out(V, F, centre):
    c = V[F].mean(1); n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    flip = np.einsum('ij,ij->i', n, c - centre) < 0
    F = F.copy(); F[flip] = F[flip][:, [0, 2, 1]]
    return V, F


class Collider:
    """What a garment may not pass through: posed meshes as a point-normal surface,
    and a vehicle's seat, back and boards as solid blocks."""
    def __init__(self, parts, boxes=(), reach=.07):
        P = []; N = []
        for posed, faces in parts:
            W, G, _, _ = weld(posed, faces)
            P.append(W); N.append(vertex_normals(W, G))
        self.P = np.concatenate(P); self.N = np.concatenate(N); self.tree = cKDTree(self.P)
        self.boxes = [(np.array(b['lo']), np.array(b['hi'])) for b in boxes]; self.reach = reach

    def push(self, X, margin):
        hit = np.zeros(len(X), bool)
        d, i = self.tree.query(X, k=1)
        n = self.N[i]; depth = np.einsum('ij,ij->i', X - self.P[i], n)
        m = (depth < margin) & (d < self.reach)
        X[m] += n[m] * (margin - depth[m])[:, None]; hit |= m
        for lo, hi in self.boxes:
            inside = np.all((X > lo - margin) & (X < hi + margin), axis=1)
            if not inside.any(): continue
            Y = X[inside]
            gaps = np.c_[Y - (lo - margin), (hi + margin) - Y]   # distance to each face
            k = np.argmin(gaps, axis=1)
            axis = k % 3; sign = np.where(k < 3, -1., 1.)
            Y[np.arange(len(Y)), axis] += sign * gaps[np.arange(len(Y)), k]
            X[inside] = Y; hit |= inside
        return hit


# ---------------------------------------------------------------- shell
def shell(S, col, g, clearance):
    """Cut from the body's garment `g['from']`, stood off by its loft and smoothed."""
    src = S['meshes'][g['from']]
    W, G, idx, inv = weld(src['posed'], src['faces'])
    joints = src['joints'][idx]; weights = src['weights'][idx]
    name = S['joints']
    dom = np.array([name[j[np.argmax(w)]] for j, w in zip(joints, weights)])
    sleeve = np.array([d.startswith(('upperarm', 'lowerarm', 'hand')) for d in dom])
    lower_arm = np.array([d.startswith(('lowerarm', 'hand')) for d in dom])
    N = vertex_normals(W, G)
    loft = np.where(sleeve, g['sleeve_loft_m'], g['loft_m'])
    # The cuff eases out over the last 12 cm of the forearm.
    hand = {'l': S['bones']['hand_l'], 'r': S['bones']['hand_r']}
    to_hand = np.minimum(np.linalg.norm(W - hand['l'], axis=1), np.linalg.norm(W - hand['r'], axis=1))
    loft = loft + np.where(lower_arm, g['cuff_flare_m'] * np.clip(1 - (to_hand - .05) / .12, 0, 1), 0)
    neck_base = g['collar_from_y_m']
    collar = W[:, 1] > neck_base
    loft = np.where(collar, g['collar_loft_m'] + (W[:, 1] - neck_base) * g['collar_flare'], loft)
    X = W + N * loft[:, None]
    E = edges(G)
    boundary = boundary_vertices(G)
    ease = g.get('ease')
    if ease: X = eased(S, X, W, N, dom, sleeve, collar, ease)
    floor = np.einsum('ij,ij->i', X - W, N)            # how far off the body each point stands
    for _ in range(g['smooth_iterations']):
        for f in (.5, -.53):              # Taubin: smooth without shrinking
            L = laplacian(X, E, len(X)); L[boundary] *= .35
            X = X + f * L
        col.push(X, clearance)
    for _ in range(ease.get('hull_iterations', 0) if ease else 0):
        # A heavy cloth bridges the body's hollows: smooth, but never back in toward
        # the body past where the ease stood it.
        L = laplacian(X, E, len(X)); L[boundary] *= .35; L[collar] = 0      # the collar keeps its fit
        X = X + .5 * L
        d = np.einsum('ij,ij->i', X - W, N)
        X += N * np.maximum(floor - d, 0)[:, None]
        col.push(X, clearance)
    if g.get('elbow_creases'): X = sleeve_creases(S, X, vertex_normals(X, G), dom, g['elbow_creases'])
    for _ in range(4): col.push(X, clearance)
    return dict(posed=X, faces=G, joints=joints, weights=weights)


def lap_folds(S, grid, faces, f, col, clearance):
    """Gathered folds where a seated coat's skirt bunches over the lap: ridges that
    radiate from a point between the hips and run down along the thighs, as the
    cloth gathered at the waist spreads over them. Displaced along the cloth's own
    normal on the rows that lie face-up on the thighs, then held clear of the body."""
    R, C, _ = grid.shape
    X = grid.reshape(-1, 3).copy()
    n = vertex_normals(X, faces)
    hub = (S['bones']['thigh_l'] + S['bones']['thigh_r']) / 2 + np.array(f.get('hub_offset_m', [0, 0, 0]))
    th = np.arctan2(X[:, 0] - hub[0], X[:, 2] - hub[2])
    k = 2 * np.pi * f['radius_m'] / f['wavelength_m']
    rng = np.random.default_rng(f.get('seed', 1))
    ph = rng.uniform(0, 2 * np.pi, 3)
    wave = np.sin(k * th + ph[0] + .6 * np.sin(.37 * k * th + ph[1])) * (.75 + .25 * np.sin(.21 * k * th + ph[2]))
    row = np.repeat(np.arange(R) * 1.0, C) / max(R - 1, 1)
    s = row * (R - 1) * f['row_m']
    a, b = f['rows_m']
    env = np.clip((s - a) / .05, 0, 1) * np.clip((b - s) / .08, 0, 1)
    up = np.clip((n[:, 1] - f.get('facing_up', .3)) / .3, 0, 1)
    X += n * (f['amp_m'] * (.5 + .5 * wave) * env * up)[:, None]       # ridges stand up off the lap
    for _ in range(3): col.push(X, clearance)
    return X.reshape(R, C, 3)


def sleeve_creases(S, X, N, dom, e):
    """Creases round the crook of a bent elbow: a few ridges across the sleeve, deepest
    on the inside of the bend."""
    B = S['bones']; X = X.copy()
    for side in ('l', 'r'):
        el = B[f'lowerarm_{side}']; ua = el - B[f'upperarm_{side}']; fa = B[f'hand_{side}'] - el
        ua /= np.linalg.norm(ua); fa /= np.linalg.norm(fa)
        inside = fa - ua; inside /= np.linalg.norm(inside) + 1e-12     # toward the crook
        m = np.array([d.endswith('_' + side) and d.startswith(('upperarm', 'lowerarm')) for d in dom])
        V = X[m] - el
        axis = np.where((V @ ua)[:, None] < 0, ua, fa)
        along = np.einsum('ij,ij->i', V, axis)                            # signed distance from the elbow
        rad = V - axis * along[:, None]; rad /= np.linalg.norm(rad, axis=1)[:, None] + 1e-12
        crook = np.clip(np.einsum('ij,j->i', rad, inside), 0, 1) ** .7 * .8 + .2
        env = np.clip(1 - np.abs(along) / e['reach_m'], 0, 1)
        X[m] += N[m] * (e['amp_m'] * np.sin(2 * np.pi * along / e['wavelength_m']) * env * crook)[:, None]
    return X


def _nearest_on_chain(V, chain):
    """Each point's nearest point on a polyline of bone heads, and that segment's direction."""
    best = np.full(len(V), np.inf); P = np.zeros_like(V); T = np.zeros_like(V)
    for a, b in zip(chain[:-1], chain[1:]):
        ab = b - a; t = np.clip(((V - a) @ ab) / (ab @ ab), 0, 1)
        Q = a + t[:, None] * ab; d = np.linalg.norm(V - Q, axis=1); m = d < best
        best[m] = d[m]; P[m] = Q[m]; T[m] = ab / np.linalg.norm(ab)
    return P, T


def eased(S, X, W, N, dom, sleeve, collar, e):
    """Stand a heavy coat off the figure: out from the spine by `chest_m` (fuller in front
    by `front_bias`, over a band of heights), out from each arm's bones by `sleeve_m`
    (armhole to cuff), and square at the shoulder by `shoulder_m`. The collar keeps its fit."""
    B = S['bones']
    X = X.copy()
    torso = ~sleeve & ~collar
    spine = np.array([B[k] for k in ('pelvis', 'spine_01', 'spine_02', 'spine_03', 'neck_01')])
    P, T = _nearest_on_chain(W, spine)
    R = W - P; R -= T * np.einsum('ij,ij->i', R, T)[:, None]
    R /= np.linalg.norm(R, axis=1)[:, None] + 1e-12
    lo, hi = e['chest_band_y_m']; fade = e.get('band_fade_m', .08)
    band = np.clip((W[:, 1] - (lo - fade)) / fade, 0, 1) * np.clip(((hi + fade) - W[:, 1]) / fade, 0, 1)
    fwd = np.clip(R[:, 2], 0, 1)                         # +z is the figure's front
    amt = e['chest_m'] * band * (1 + e.get('front_bias', 0) * fwd)
    X[torso] += R[torso] * amt[torso, None]
    for side in ('l', 'r'):
        arm = np.array([B[f'clavicle_{side}'] * .5 + B[f'upperarm_{side}'] * .5, B[f'upperarm_{side}'],
                        B[f'lowerarm_{side}'], B[f'hand_{side}']])
        m = sleeve & np.array([d.endswith('_' + side) for d in dom])
        if not m.any(): continue
        Pa, Ta = _nearest_on_chain(W[m], arm)
        Ra = W[m] - Pa; Ra -= Ta * np.einsum('ij,ij->i', Ra, Ta)[:, None]
        Ra /= np.linalg.norm(Ra, axis=1)[:, None] + 1e-12
        along = np.linalg.norm(W[m] - B[f'upperarm_{side}'], axis=1)
        reach = np.linalg.norm(B[f'hand_{side}'] - B[f'upperarm_{side}'])
        s0, s1 = e['sleeve_m']
        X[m] += Ra * (s0 + (s1 - s0) * np.clip(along / reach, 0, 1))[:, None]
        # Square the shoulder: lift the top of the armhole outward and up.
        sh = B[f'upperarm_{side}']
        near = np.clip(1 - np.linalg.norm(W - sh, axis=1) / e.get('shoulder_reach_m', .11), 0, 1) * (W[:, 1] > sh[1] - .02) * ~collar
        out = np.array([1. if side == 'l' else -1., .6, 0]); out /= np.linalg.norm(out)
        X += out * (e.get('shoulder_m', 0) * near)[:, None]
    return X


# ---------------------------------------------------------------- gloves
HAND_BONES = ('hand', 'thumb', 'index', 'middle', 'ring', 'pinky')


def gloves(S, g):
    """Gloves cut from the body's own hands: every face skinned to a hand or finger bone,
    and the forearm for `gauntlet_m` above the wrist; stood off by `loft_m` (the leather or
    cotton), the gauntlet flaring by `gauntlet_flare_m` so it rides over the shirt cuff,
    smoothed so knuckles and nails no longer show."""
    src = S['meshes'][g.get('from', 'body_0')]
    W, G, idx, inv = weld(src['posed'], src['faces'])
    joints = src['joints'][idx]; weights = src['weights'][idx]
    name = S['joints']
    dom = np.array([name[j[np.argmax(w)]] for j, w in zip(joints, weights)])
    hand = np.array([d.startswith(HAND_BONES) for d in dom])
    up = np.zeros(len(W))
    keep = hand.copy()
    for side in ('l', 'r'):
        wrist = S['bones'][f'hand_{side}']; elbow = S['bones'][f'lowerarm_{side}']
        ax = (elbow - wrist) / np.linalg.norm(elbow - wrist)
        s = (W - wrist) @ ax
        fore = dom == f'lowerarm_{side}'
        m = fore & (s > -.02) & (s < g['gauntlet_m'])
        keep |= m; up = np.where(m, np.clip(s / g['gauntlet_m'], 0, 1), up)
    F = G[keep[G].all(1)]
    used = np.unique(F); remap = -np.ones(len(W), int); remap[used] = np.arange(len(used))
    F = remap[F]; W = W[used]; up = up[used]; joints = joints[used]; weights = weights[used]
    N = vertex_normals(W, F)
    X = W + N * (g['loft_m'] + g['gauntlet_flare_m'] * up ** 1.5)[:, None]
    E = edges(F); boundary = boundary_vertices(F)
    for _ in range(g.get('smooth_iterations', 6)):
        for f in (.5, -.53):
            L = laplacian(X, E, len(X)); L[boundary] *= .35
            X = X + f * L
    return dict(posed=X, faces=F, joints=joints, weights=weights)


# ---------------------------------------------------------------- draped cloth
def drape(top, centre, rows, row_m, fullness, col, dyn, lift=.25, bend_h=.12, init=None, friction=.25, closed_rows=0):
    """Hang a cloth from `top` (C x 3, ordered round `centre`, open at the front)
    and let it fall. `init` (C x 3), if given, is each column's starting direction
    instead of straight out from the centre (a coat's front laid along the thighs);
    `friction` is the share of its speed a cloth point keeps when it touches;
    `closed_rows` joins the front edges for that many rows from the top (a coat
    buttoned over the lap), so the cloth bridges the thighs instead of sliding off.
    Returns (R x C x 3) positions and the triangle grid."""
    C = len(top); R = rows
    out = top - centre; out[:, 1] = 0; out /= np.linalg.norm(out, axis=1)[:, None]
    if init is not None: out = init
    s = np.arange(R) * row_m
    X = top[None] + out[None] * (s[:, None, None] * .92) + np.array([0, 1, 0]) * (s[:, None, None] * lift)
    prev = X.copy()
    top_len = np.linalg.norm(np.diff(top, axis=0), axis=1)              # (C-1)
    grow = 1 + (fullness - 1) * (s / s[-1])
    Lh = top_len[None] * grow[:, None]                                   # (R, C-1)
    Lv = row_m
    Lc = np.linalg.norm(top[0] - top[-1]) * grow[:closed_rows]
    inv_mass = np.ones((R, C)); inv_mass[0] = 0
    g = np.array([0, -9.81, 0]) * dyn['dt_s'] ** 2
    clearance = dyn['clearance_m']
    for step in range(dyn['steps']):
        vel = (X - prev) * .985
        prev = X.copy()
        X = X + vel + g * inv_mass[..., None]
        for _ in range(dyn['iterations']):
            D = np.zeros_like(X); K = np.zeros((R, C))
            def link(a_sl, b_sl, L, k=1.):
                A = X[a_sl]; B = X[b_sl]; d = B - A
                ln = np.linalg.norm(d, axis=-1); ln = np.maximum(ln, 1e-9)
                corr = (d * ((ln - L) / ln)[..., None]) * .5 * k
                D[a_sl] += corr; D[b_sl] -= corr; K[a_sl] += 1; K[b_sl] += 1
            link((slice(None), slice(0, -1)), (slice(None), slice(1, None)), Lh)
            link((slice(0, -1), slice(None)), (slice(1, None), slice(None)), Lv)
            diag = np.sqrt(Lh[:-1] ** 2 + Lv ** 2)
            link((slice(0, -1), slice(0, -1)), (slice(1, None), slice(1, None)), diag, .7)
            link((slice(0, -1), slice(1, None)), (slice(1, None), slice(0, -1)), diag, .7)
            link((slice(0, -2), slice(None)), (slice(2, None), slice(None)), 2 * Lv, .25)    # bend
            link((slice(None), slice(0, -2)), (slice(None), slice(2, None)), Lh[:, :-1] + Lh[:, 1:], bend_h)
            if closed_rows: link((slice(0, closed_rows), 0), (slice(0, closed_rows), C - 1), Lc)
            X = X + 1.5 * D / np.maximum(K, 1)[..., None] * inv_mass[..., None]
        flat = X.reshape(-1, 3)
        hit = col.push(flat, clearance)
        X = flat.reshape(R, C, 3)
        hp = hit.reshape(R, C)
        prev[hp] = X[hp] - (X[hp] - prev[hp]) * friction          # contact friction
        X[0] = top; prev[0] = top
    for _ in range(dyn['relax_passes']):
        for f in (.5, -.53):
            L = np.zeros_like(X); n = np.zeros((R, C, 1))
            L[1:] += X[:-1]; n[1:] += 1; L[:-1] += X[1:]; n[:-1] += 1
            L[:, 1:] += X[:, :-1]; n[:, 1:] += 1; L[:, :-1] += X[:, 1:]; n[:, :-1] += 1
            X = X + f * (L / n - X) * inv_mass[..., None]
        flat = X.reshape(-1, 3); col.push(flat, clearance); X = flat.reshape(R, C, 3)
    F = []
    for i in range(R - 1):
        for j in range(C - 1):
            a, b, c, d = i * C + j, i * C + j + 1, (i + 1) * C + j, (i + 1) * C + j + 1
            F += [[a, c, b], [b, c, d]]
    for i in range(max(0, min(closed_rows, R) - 1)):          # the closed front's own strip
        a, b, c, d = i * C + C - 1, i * C, (i + 1) * C + C - 1, (i + 1) * C
        F += [[a, c, b], [b, c, d]]
    return X, np.array(F)


def ring_from_loop(P, loop, centre, count, open_front=True, inset=.004, rise=.01):
    """Resample a closed loop by angle round `centre`, starting and ending at the
    front (+z), inset toward the centre so the hung cloth tucks under the coat."""
    Q = P[loop]
    ang = np.arctan2(Q[:, 0] - centre[0], Q[:, 2] - centre[2])
    order = np.argsort(ang); Q = Q[order]; ang = ang[order]
    Qc = np.r_[Q[-1:], Q, Q[:1]]; ac = np.r_[ang[-1:] - 2 * np.pi, ang, ang[:1] + 2 * np.pi]
    gap = .03 if open_front else 0
    want = np.linspace(gap, 2 * np.pi - gap, count)               # from the front, round by the left
    want = np.where(want > np.pi, want - 2 * np.pi, want)
    out = np.stack([np.interp(want, ac, Qc[:, k]) for k in range(3)], axis=1)
    d = out - centre; d[:, 1] = 0
    out = out - d / np.linalg.norm(d, axis=1)[:, None] * inset
    out[:, 1] += rise
    return out


def hem_ring(parent, g):
    loops = boundary_loops(parent['faces'])
    hem = min(loops, key=lambda l: parent['posed'][l, 1].mean())
    centre = parent['posed'][hem].mean(0)
    return ring_from_loop(parent['posed'], hem, centre, g['ring_count'], inset=g['inset_m'], rise=g['rise_m']), centre


def collar_ring(S, parent, g):
    """Round the collar's foot: the shell's outermost point in each direction from the
    neck, in a band of heights."""
    X = parent['posed']
    neck = S['bones'][g.get('neck_bone', 'neck_01')]
    lo, hi = g['band_y_m']
    band = np.where((X[:, 1] > lo) & (X[:, 1] < hi) & (np.hypot(X[:, 0] - neck[0], X[:, 2] - neck[2]) < g['band_radius_m']))[0]
    neck_c = X[band].mean(0)
    ang = np.arctan2(X[band, 0] - neck_c[0], X[band, 2] - neck_c[2])
    ring = []
    half = g['ring_half_count']
    for a in np.r_[np.linspace(.04, np.pi, half)[:-1], np.linspace(-np.pi, -.04, half)]:
        dirn = np.array([math.sin(a), 0, math.cos(a)])
        cand = band[np.abs(((ang - a + np.pi) % (2 * np.pi)) - np.pi) < g['angular_window_rad']]
        far = cand[np.argmax((X[cand] - neck_c) @ dirn)]
        ring.append(X[far] + dirn * g['outset_m'] + [0, g['rise_m'], 0])
    return np.array(ring), neck_c


# ---------------------------------------------------------------- hats
def hat(S, g):
    """A hat on the head's own cross-section at `base_y_m`: a crown of rings by the
    profile [[height fraction, flare], ...], a brim wider fore and aft or at the
    sides, curling up at the sides and drooping fore and aft, and a band."""
    hair = S['meshes'][g.get('hair_mesh', 'short04_hair')]['posed']; body = S['meshes'][g.get('body_mesh', 'body_0')]['posed']
    base_y = g['base_y_m']
    head = np.r_[hair, body[body[:, 1] > base_y - .05]]
    band = head[np.abs(head[:, 1] - base_y) < .012]
    cx, cz = (band[:, 0].max() + band[:, 0].min()) / 2, (band[:, 2].max() + band[:, 2].min()) / 2
    rx = (band[:, 0].max() - band[:, 0].min()) / 2 + g['ease_m']
    rz = (band[:, 2].max() - band[:, 2].min()) / 2 + g['ease_m']
    seg = 40; th = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    ring = lambda sx, sz, y: np.c_[cx + sx * np.sin(th), np.full(seg, y), cz + sz * np.cos(th)]
    H_ = g['crown_height_m']
    crown = [ring(rx * f, rz * f, base_y + H_ * t) for t, f in g['crown_profile']]
    side = np.abs(np.sin(th)); fore = np.abs(np.cos(th))
    bw = g['brim_side_m'] * side + g['brim_fore_m'] * fore
    curl = g['brim_curl_m'] * side ** 2 - g.get('brim_droop_m', 0) * fore ** 2
    thick = g.get('brim_thickness_m', .005)
    def brim(off, dy, k):
        return np.c_[cx + (rx + off * k) * np.sin(th), np.broadcast_to(base_y + dy, th.shape), cz + (rz + off * k) * np.cos(th)]
    brim_mid = brim(bw * .6, curl * .3 - .002, 1)
    brim_out = brim(bw, curl, 1)
    brim_out_lo = brim_out - [0, thick, 0]
    brim_mid_lo = brim(bw * .6, curl * .3 - .002 - thick, 1)
    under = brim(0 * bw, -.002 - thick, 1)
    rings_hat = [under, brim_mid_lo, brim_out_lo, brim_out, brim_mid] + crown
    V = np.concatenate(rings_hat)
    F = []
    for r in range(len(rings_hat) - 1):
        for j in range(seg):
            a, b = r * seg + j, r * seg + (j + 1) % seg
            c, d = a + seg, b + seg
            F += [[a, b, c], [b, d, c]]
    top_t, top_f = g['crown_profile'][-1]
    top_c = len(V); V = np.r_[V, [[cx, base_y + H_ * top_t + g.get('crown_dome_m', 0), cz]]]
    t0 = (len(rings_hat) - 1) * seg
    for j in range(seg): F.append([t0 + j, t0 + (j + 1) % seg, top_c])
    F = np.array(F)
    if g.get('crown_crease_m'):
        # A pinched crown: the top's centre pressed down into a crease front to back.
        top = V[top_c].copy(); top[1] -= g['crown_crease_m']; V[top_c] = top
    V, F = orient_out(V, F, np.array([cx, base_y + H_ * .5, cz]))
    band_lo, band_hi = base_y + .002, base_y + g['band_height_m']
    f_lo = np.interp(.002 / H_, [t for t, _ in g['crown_profile']], [f for _, f in g['crown_profile']])
    f_hi = np.interp(g['band_height_m'] / H_, [t for t, _ in g['crown_profile']], [f for _, f in g['crown_profile']])
    bring = [ring(rx * (f_lo + .008), rz * (f_lo + .008), band_lo), ring(rx * (f_hi + .0035), rz * (f_hi + .0035), band_hi)] \
        if g.get('band_follows_profile') else \
        [ring(rx * 1.008, rz * 1.008, band_lo), ring(rx * 1.0035, rz * 1.0035, band_hi)]
    BV = np.concatenate(bring); BF = []
    for j in range(seg):
        a, b = j, (j + 1) % seg; BF += [[a, b, a + seg], [b, b + seg, a + seg]]
    BV, BF = orient_out(BV, np.array(BF), np.array([cx, base_y + .02, cz]))
    return (V, F), (BV, BF), dict(base_y_m=base_y, centre_xz_m=[cx, cz], inner_radii_m=[rx, rz])


# ---------------------------------------------------------------- buttons
def buttons(parent, g):
    X = parent['posed']; N = vertex_normals(X, parent['faces'])
    out_v, out_f = [], []
    r = g['radius_m']; seg = 10
    th = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    for x in g['rows_x_m']:
        for y in np.linspace(*g['y_range_m'], g['per_row']):
            near = np.abs(X[:, 1] - y) < .02
            cand = np.where(near & (np.abs(X[:, 0] - x) < .02))[0]
            i = cand[np.argmax(X[cand, 2])]
            n = N[i]; p = X[i] + n * .002
            u = np.cross(n, [0, 1, 0]); u /= np.linalg.norm(u); v = np.cross(n, u)
            base = len(sum(out_v, [])) if out_v else 0
            ring_lo = [p + r * (math.cos(t) * u + math.sin(t) * v) for t in th]
            ring_hi = [p + n * .0035 + .8 * r * (math.cos(t) * u + math.sin(t) * v) for t in th]
            verts = ring_lo + ring_hi + [p + n * .0045]
            f = []
            for j in range(seg):
                a, b = j, (j + 1) % seg
                f += [[a, b, seg + a], [b, seg + b, seg + a], [seg + a, seg + b, 2 * seg]]
            out_v.append(verts); out_f.append(np.array(f) + base)
    return np.array(sum(out_v, [])), np.concatenate(out_f)


# ---------------------------------------------------------------- skinning
def bind(S, posed, joints, weights):
    """Unpose positions through the dressed pose's linear-blend matrices to bind space."""
    M = np.einsum('vn,vnij->vij', weights, S['joint_m'][joints])
    return np.einsum('vij,vj->vi', np.linalg.inv(M), np.c_[posed, np.ones(len(posed))])[:, :3]


def nearest_weights(S, X, sources, k=6, remap=None):
    P = np.concatenate([S['meshes'][s]['posed'] for s in sources])
    J = np.concatenate([S['meshes'][s]['joints'] for s in sources])
    Wt = np.concatenate([S['meshes'][s]['weights'] for s in sources])
    tree = cKDTree(P); d, idx = tree.query(X, k=k)
    w = 1 / np.maximum(d, 1e-4) ** 2
    nj = len(S['joints']); acc = np.zeros((len(X), nj))
    for c in range(k):
        np.add.at(acc, (np.arange(len(X))[:, None], J[idx[:, c]]), Wt[idx[:, c]] * w[:, c, None])
    if remap:
        for a, b in remap.items():
            ia, ib = S['joints'].index(a), S['joints'].index(b); acc[:, ib] += acc[:, ia]; acc[:, ia] = 0
    top = np.argsort(-acc, axis=1)[:, :4]
    tw = np.take_along_axis(acc, top, axis=1); tw /= tw.sum(1)[:, None]
    return top, tw


def rigid(S, n, joint):
    return np.full((n, 4), S['joints'].index(joint)), np.tile([1., 0, 0, 0], (n, 1))


# ---------------------------------------------------------------- spring tails
def add_tails(S, cloth, spec):
    """Give a draped cloth spring tails. `cloth` = dict(grid R x C x 3, centre, joints,
    weights). Angles are degrees round the hang centre from the front, by his left:
    0 front, 90 his left, 180 the back, 270 his right; a cloth open at the front does
    not wrap there. Each vertex shares `share` of its weight (by row, or by how far it
    hangs below a height) between the two tails that bracket its angle. A tail's head
    is where its column starts to hang free, its tip the hem. Returns the new (joints,
    weights) and the tail records; S gains the tail joints, whose pose matrix is their
    parent's, so the drape is unchanged at rest."""
    G = cloth['grid']; R, C, _ = G.shape; centre = cloth['centre']
    flat = G.reshape(-1, 3)
    ang_c = np.degrees(np.arctan2(G[0, :, 0] - centre[0], G[0, :, 2] - centre[2])) % 360
    tails = sorted(spec['tails'], key=lambda t: t['angle_deg'])
    t_ang = np.array([t['angle_deg'] for t in tails], float)
    # Share: how free this point of the cloth hangs.
    rows = np.repeat(np.arange(R), C) / max(R - 1, 1)
    sh = spec['share']
    if sh['by'] == 'row': free = rows ** sh.get('power', 1.0)
    elif sh['by'] == 'below_y': free = np.clip((sh['y_m'] - flat[:, 1]) / sh['fall_m'], 0, 1)
    else: raise SystemExit(f'wardrobe: unknown tail share {sh["by"]}')
    free_g = free.reshape(R, C)
    records = []
    for t in tails:
        col = int(np.argmin(np.abs(ang_c - t['angle_deg'])))
        hang = np.where(free_g[:, col] > 0)[0]
        r0 = max(int(hang[0]) - 1, 0) if len(hang) else 0
        head = G[r0, col]; tip = G[-1, col]
        p = S['joints'].index(t['parent'])
        M = S['joint_m'][p]
        head_b = (np.linalg.inv(M) @ np.r_[head, 1])[:3]; tip_b = (np.linalg.inv(M) @ np.r_[tip, 1])[:3]
        name = t['name']
        if name in S['joints']: raise SystemExit(f'wardrobe: tail {name} is already a joint')
        ib = np.eye(4); ib[:3, 3] = -head_b
        S['joints'].append(name); S['joint_m'] = np.r_[S['joint_m'], M[None]]; S['ibm'] = np.r_[S['ibm'], ib[None]]
        records.append(dict(name=name, parent=t['parent'], angle_deg=t['angle_deg'], head_bind_m=np.round(head_b, 6).tolist(),
                            tip_bind_m=np.round(tip_b, 6).tolist(), frequency_hz=t['frequency_hz'],
                            damping_ratio=t['damping_ratio'], max_deg=t['max_deg'], index=len(S['joints']) - 1))
    share = sh['max'] * free
    # Blend between the two tails bracketing each column's angle; past the end tails, the end tail.
    ang_v = np.clip(np.tile(ang_c, R), t_ang[0], t_ang[-1])
    k = np.clip(np.searchsorted(t_ang, ang_v) - 1, 0, max(len(t_ang) - 2, 0))
    if len(t_ang) == 1: k[:] = 0; f = np.zeros(len(ang_v)); kb = k
    else:
        kb = k + 1; span = t_ang[kb] - t_ang[k]; f = (ang_v - t_ang[k]) / np.maximum(span, 1e-9)
    a_id = np.array([records[i]['index'] for i in k]); b_id = np.array([records[i]['index'] for i in kb])
    J0, W0 = cloth['joints'], cloth['weights']
    nj = len(S['joints']); acc = np.zeros((len(flat), nj))
    np.add.at(acc, (np.arange(len(flat))[:, None], J0), W0 * (1 - share)[:, None])
    np.add.at(acc, (np.arange(len(flat)), a_id), share * (1 - f))
    np.add.at(acc, (np.arange(len(flat)), b_id), share * f)
    top = np.argsort(-acc, axis=1)[:, :4]
    tw = np.take_along_axis(acc, top, axis=1); tw /= tw.sum(1)[:, None]
    for r in records: r.pop('index')
    return top, tw, records


# ---------------------------------------------------------------- provenance
def source_ids(scene):
    p = APP / 'data' / 'sidecars' / scene / 'sources' / 'index.json'
    return {s['source_id'] if isinstance(s, dict) else s for s in json.loads(p.read_text())['sources']} if p.exists() else set()


def liberty_ids():
    text = (APP / 'docs' / 'LIBERTIES.md').read_text()
    return set(re.findall(r'^### (L[\w-]+)', text, flags=re.M))


def provenance_errors(recipe):
    """Every garment states a grade and the sources it rests on or the liberty that
    records it; every source and liberty it names exists."""
    errors = []
    known_src = source_ids(recipe['scene']); known_lib = liberty_ids()
    for g in recipe['garments']:
        p = g.get('provenance') or {}
        if p.get('grade') not in GRADES: errors.append(f'{g["name"]}: no grade')
        if not p.get('source_ids') and not p.get('liberty'): errors.append(f'{g["name"]}: neither a source nor a liberty')
        if p.get('source_ids') and not p.get('source_scope'): errors.append(f'{g["name"]}: sources without their scope')
        for s in p.get('source_ids', []):
            if s not in known_src: errors.append(f'{g["name"]}: unknown source {s}')
        if p.get('liberty') and p['liberty'] not in known_lib: errors.append(f'{g["name"]}: unknown liberty {p["liberty"]}')
        if p.get('grade') == 'attested' and not p.get('source_ids'): errors.append(f'{g["name"]}: attested without a source')
    return errors


# ---------------------------------------------------------------- build
def build(recipe):
    S = dressed(recipe['body_master'], recipe['asset_id'], recipe['clip_posed'])
    dyn = recipe['drape_dynamics']
    boxes = recipe.get('vehicle_box_colliders', [])
    body_parts = [(S['meshes'][k]['posed'], S['meshes'][k]['faces']) for k in recipe['collide_with_body_meshes']]
    col = Collider(body_parts, boxes)
    made, parts, fits, tails = {}, [], {}, []

    def add(name, material, posed, faces, joints, weights):
        parts.append(dict(name=name, material=material, posed=posed, faces=faces, joints=joints, weights=weights))

    for g in recipe['garments']:
        kind = g['kind']
        if kind == 'shell':
            sh = shell(S, col, g, dyn['clearance_m'])
            made[g['name']] = sh
            add(g['name'], g['material'], sh['posed'], sh['faces'], sh['joints'], sh['weights'])
        elif kind in ('drape_hem', 'drape_collar'):
            parent = made[g['hang_from']]
            if kind == 'drape_hem': top, centre = hem_ring(parent, g)
            else: top, centre = collar_ring(S, parent, g)
            c = col if not g.get('collide_with_parent') else Collider(body_parts + [(parent['posed'], parent['faces'])], boxes)
            grid, faces = drape(top, centre, int(round(g['length_m'] / g['row_m'])) + 1, g['row_m'], g['hem_fullness'], c, dyn,
                                lift=g['lift'], bend_h=g['bend_h'], friction=g.get('friction', .25),
                                closed_rows=int(round(g.get('closed_front_m', 0) / g['row_m'])))
            if g.get('lap_folds'):
                grid = lap_folds(S, grid, faces, dict(g['lap_folds'], row_m=g['row_m']), c, dyn['clearance_m'])
            X = grid.reshape(-1, 3)
            J, W = nearest_weights(S, X, g['weights_from'], remap=g.get('weights_remap'))
            if g.get('spring_tails'):
                J, W, rec = add_tails(S, dict(grid=grid, centre=centre, joints=J, weights=W), g['spring_tails'])
                for r in rec: r['garment'] = g['name']
                tails += rec
            add(g['name'], g['material'], X, faces, J, W)
        elif kind == 'hat':
            (V, F), (BV, BF), fit = hat(S, g)
            fits[g['name']] = fit
            add(g['name'], g['material'], V, F, *rigid(S, len(V), 'head'))
            add(g['name'] + '_band', g['band_material'], BV, BF, *rigid(S, len(BV), 'head'))
        elif kind == 'gloves':
            gv = gloves(S, g)
            add(g['name'], g['material'], gv['posed'], gv['faces'], gv['joints'], gv['weights'])
        elif kind == 'buttons':
            V, F = buttons(made[g['on']], g)
            add(g['name'], g['material'], V, F, *nearest_weights(S, V, g['weights_from'], k=3))
        else:
            raise SystemExit(f'wardrobe: unknown garment kind {kind}')
    for p in parts:
        p['bind'] = bind(S, p['posed'], p['joints'], p['weights'])
        n = vertex_normals(p['posed'], p['faces'])
        M = np.einsum('vn,vnij->vij', p['weights'], S['joint_m'][p['joints']])[:, :3, :3]
        nb = np.einsum('vij,vj->vi', np.linalg.inv(M), n)        # rigid-ish: inverse rotation
        p['normal'] = nb / (np.linalg.norm(nb, axis=1)[:, None] + 1e-12)
    return S, merge_by_material(parts), fits, tails


def merge_by_material(parts):
    """One mesh (one draw) per material: a coat's body, skirt and cape are one cloth."""
    out = {}
    for p in parts:
        q = out.get(p['material'])
        if q is None: out[p['material']] = dict(p, name=p['name'], faces=p['faces'].copy()); continue
        off = len(q['bind'])
        for k in ('bind', 'normal', 'joints', 'weights', 'posed'): q[k] = np.concatenate([q[k], p[k]])
        q['faces'] = np.concatenate([q['faces'], p['faces'] + off]); q['name'] += '+' + p['name']
    return list(out.values())


def b64(a, dtype): return base64.b64encode(np.ascontiguousarray(a, dtype=dtype).tobytes()).decode()


def document(recipe, recipe_path, S, parts, fits, tails):
    nb = S['body_joints']
    used = sorted({int(j) for p in parts for j, w in zip(p['joints'].ravel(), p['weights'].ravel()) if w > 0 and j < nb}
                  | {S['joints'].index(t['parent']) for t in tails})
    used += [S['joints'].index(t['name']) for t in tails]
    remap = {j: i for i, j in enumerate(used)}
    out_parts = []
    for p in parts:
        J = np.vectorize(lambda j: remap.get(int(j), 0))(p['joints']); J[p['weights'] == 0] = 0
        out_parts.append(dict(name=p['name'], material=p['material'], vertex_count=int(len(p['bind'])),
                              triangle_count=int(len(p['faces'])),
                              position=b64(np.round(p['bind'], 6), '<f4'), normal=b64(np.round(p['normal'], 5), '<f4'),
                              joints=b64(J, '<u1'), weights=b64(np.round(p['weights'], 5), '<f4'),
                              index=b64(p['faces'].ravel(), '<u2' if len(p['bind']) < 65536 else '<u4')))
    vehicle = recipe.get('vehicle')
    garments = []
    for g in recipe['garments']:
        p = g['provenance']
        garments.append(dict(name=g['name'], kind=g['kind'], material=g['material'], **p))
    return dict(
        schema=SCHEMA, ticket=recipe['tickets'], asset_id=recipe['asset_id'], scene=recipe['scene'],
        clip_posed=recipe['clip_posed'], body_master=recipe['body_master'], body_master_sha256=S['sha'],
        vehicle=vehicle, vehicle_glb_sha256=sha((APP / vehicle).read_bytes()) if vehicle else None,
        recipe=recipe_path, recipe_sha256=sha((APP / recipe_path).read_bytes()),
        grade=recipe['grade'], liberty=recipe['liberty'], license='CC0-1.0',
        producer='tools/human_wardrobe.py', basis=recipe['basis'],
        garments=garments, drape_dynamics=recipe['drape_dynamics'],
        materials=recipe['materials'], recolor_body_materials=recipe.get('recolor_body_materials', {}),
        vehicle_box_colliders=recipe.get('vehicle_box_colliders', []), hat_fit=fits,
        joints=[S['joints'][j] for j in used],
        inverse_bind_matrices=[np.round(S['ibm'][j].T.ravel(), 7).tolist() for j in used],
        tails=tails,
        # A few vertices of each part where the producer posed them, so the renderer's
        # own skinning can be held to them (tools/test_driver_livery.mjs).
        probes=[dict(part=p['name'], index=int(i), posed_m=np.round(p['posed'][i], 6).tolist())
                for p in parts for i in np.linspace(0, len(p['bind']) - 1, 12).astype(int)],
        parts=out_parts)


def decode(doc_):
    parts = []
    for p in doc_['parts']:
        f = lambda k, dt, w: np.frombuffer(base64.b64decode(p[k]), dtype=dt).reshape(-1, w)
        parts.append(dict(name=p['name'], bind=f('position', '<f4', 3), joints=f('joints', '<u1', 4).astype(int),
                          weights=f('weights', '<f4', 4).astype(float),
                          faces=f('index', '<u2' if p['vertex_count'] < 65536 else '<u4', 3).astype(int)))
    return parts


def check(recipe, recipe_path, tolerance_m):
    """A committed wardrobe file against its recipe, its inputs and the dressed body,
    without re-draping (the drape is a long float integration and is not promised
    byte-identical across machines). Returns (errors, worst depth per part)."""
    doc_ = json.loads((APP / recipe['output']).read_text())
    S = dressed(recipe['body_master'], recipe['asset_id'], recipe['clip_posed'])
    errors = provenance_errors(recipe)
    if doc_['schema'] != SCHEMA: errors.append('schema')
    if doc_['recipe_sha256'] != sha((APP / recipe_path).read_bytes()): errors.append('the recipe changed since the file was made: rerun the producer')
    if doc_['body_master_sha256'] != S['sha']: errors.append('the body master changed since the garments were draped: rerun the producer')
    if recipe.get('vehicle') and doc_['vehicle_glb_sha256'] != sha((APP / recipe['vehicle']).read_bytes()):
        errors.append('the vehicle changed since the garments were draped: rerun the producer')
    if [g['name'] for g in doc_['garments']] != [g['name'] for g in recipe['garments']]: errors.append('garments differ from the recipe')
    tails = {t['name']: t for t in doc_.get('tails', [])}
    names = doc_['joints']
    for n, m in zip(names, doc_['inverse_bind_matrices']):
        if n in tails:
            t = tails[n]
            if t['parent'] not in names: errors.append(f'tail {n}: parent {t["parent"]} is not bound')
            want = np.eye(4); want[:3, 3] = -np.array(t['head_bind_m'])
            if np.abs(np.array(m) - want.T.ravel()).max() > 1e-5: errors.append(f'tail {n}: inverse bind is not its head')
            if not (0 < t['max_deg'] <= 30 and 0 < t['frequency_hz'] and 0 < t['damping_ratio'] <= 2): errors.append(f'tail {n}: spring out of range')
            continue
        if n not in S['joints']: errors.append(f'joint {n} is not on the body'); continue
        if np.abs(np.array(m) - S['ibm'][S['joints'].index(n)].T.ravel()).max() > 1e-5: errors.append(f'inverse bind of {n} differs')
    if set(p['material'] for p in doc_['parts']) - set(doc_['materials']): errors.append('a part names an undeclared material')
    body_parts = [(S['meshes'][k]['posed'], S['meshes'][k]['faces']) for k in recipe['collide_with_body_meshes']]
    col = Collider(body_parts, recipe.get('vehicle_box_colliders', []), reach=.05)
    # Rest pose: a tail's pose matrix is its parent's.
    JM = []
    for n in names:
        JM.append(S['joint_m'][S['joints'].index(tails[n]['parent'] if n in tails else n)])
    JM = np.array(JM)
    worst = {}
    for p in decode(doc_):
        if not np.all(np.isfinite(p['bind'])) or np.abs(p['weights'].sum(1) - 1).max() > 1e-3: errors.append(f'{p["name"]}: bad skin data')
        if p['faces'].max() >= len(p['bind']) or p['joints'].max() >= len(names): errors.append(f'{p["name"]}: index out of range'); continue
        M = np.einsum('vn,vnij->vij', p['weights'], JM[p['joints']])
        X = np.einsum('vij,vj->vi', M, np.c_[p['bind'], np.ones(len(p['bind']))])[:, :3]
        Y = X.copy(); col.push(Y, 0.0)
        worst[p['name']] = float(np.linalg.norm(Y - X, axis=1).max())
        if worst[p['name']] > tolerance_m: errors.append(f'{p["name"]}: {worst[p["name"]] * 1000:.1f} mm inside the body or the vehicle')
    return errors, worst
