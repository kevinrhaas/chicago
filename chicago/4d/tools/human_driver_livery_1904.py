# SPDX-License-Identifier: GPL-3.0-or-later
"""A coachman's box coat, shoulder cape and top hat for the 1904 brougham driver (T-3398).

Kevin, 2026-11-06, of Hans on the brougham: "his clothing is form fitting and he
looks too smooth and not real". Hans wears the 1835 donor's close shirt, waistcoat
and pantaloons and no hat. This dresses him for a private brougham's box, over those
unchanged garments, in the driver's own seated pose:

  - the coat's body and sleeves stand off the shirt by a wool's loft, smoothed so
    they no longer follow the chest and arms beneath, with a turned-up collar;
  - its skirt and the shoulder cape are DRAPED, not modelled: each is a cloth of
    particles hung from the coat and dropped under gravity (position-based dynamics)
    onto the seated body, the box cushion, the seat back and the box front, so the
    folds are where the cloth had to go;
  - a silk top hat on the head, and two rows of brass buttons down the front.

The pieces are skinned to the driver's own skeleton (weights from the nearest
garment and body points, unposed through the seated pose to the bind pose), so the
seated clip and the driver-life layer move them with him. The renderer binds them
to the loaded body's skeleton by joint name (renderers/web/js/driven-assembly-loader.js).

Every dimension and colour is a reconstructed authoring choice for a coachman of the
period, not a record of what Hans Johnson wore (liberty L-driven-town-circuits-2804).

  python3 tools/human_driver_livery_1904.py           write the livery file
  python3 tools/human_driver_livery_1904.py --check   hold the committed file to its
                                                      inputs and to the seated body
"""
from __future__ import annotations

import argparse, base64, hashlib, json, math, sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / 'tools'))
import human_working_driver_1904 as H  # noqa: E402  (load, pose, accessor, matrices)

BODY = 'assets/humans/anonymous_working_driver_1904.lod0.glb'
VEHICLE = 'renderers/web/transport/parked-brougham/brougham-near.glb'
OUT = 'renderers/web/transport/driven/driver-livery-1904.json'
SCHEMA = 'chicago4d_driver_livery_v1'

PARAMS = {
    'coat_loft_m': .022,          # the coat's body stands this far off the shirt
    'sleeve_loft_m': .017,
    'sleeve_cuff_flare_m': .012,  # extra ease at the cuff, so the sleeve does not grip the wrist
    'collar_loft_m': .012, 'collar_flare': .30,
    'smooth_iterations': 40,      # Taubin passes that take the body's anatomy out of the coat
    'clearance_m': .008,          # the least gap between the coat and what it covers
    'skirt_length_m': .76, 'skirt_row_m': .03, 'skirt_hem_fullness': 1.9,
    'cape_length_m': .27, 'cape_row_m': .025, 'cape_hem_fullness': 1.8,
    'drape_relax_passes': 6,      # light smoothing after the drape, so the folds stay and the crumple goes
    'drape_steps': 520, 'drape_iterations': 10, 'drape_dt_s': 1 / 120,
    'hat_crown_height_m': .152, 'hat_brim_side_m': .040, 'hat_brim_fore_m': .050,
    'hat_brim_curl_m': .016, 'hat_ease_m': .006,
    'buttons_per_row': 3, 'button_radius_m': .011, 'button_row_half_spacing_m': .062,
}
MATERIALS = {
    # Livery wool, a near-black blue; the cloth patch (fabric.js) weaves it as wool.
    'garment_outer__box_coat_wool': dict(color=[.034, .038, .048], roughness=.9, metalness=0, double_sided=True),
    'headwear__silk_top_hat': dict(color=[.018, .018, .020], roughness=.42, metalness=0, double_sided=False),
    'headwear__hat_band_grosgrain': dict(color=[.010, .010, .011], roughness=.7, metalness=0, double_sided=False),
    'accessory__brass_livery_buttons': dict(color=[.78, .60, .31], roughness=.35, metalness=.9, double_sided=False),
}
# The body's own garments a livery re-dyes: dark livery trousers over the donor's pale pantaloons.
RECOLOR = {'garment_lower__highwaist_pantaloons': [.040, .040, .046]}
# The vehicle's driving box, measured off brougham-near.glb (vehicle-local metres):
# the cushion's top, the seat back's face and the box front.
BOXES = [
    dict(name='cushion_and_box', lo=[-.545, .95, .555], hi=[.545, 1.7655, .955]),
    dict(name='seat_back', lo=[-.545, 1.70, .30], hi=[.545, 2.002, .587]),
    dict(name='side_rail_l', lo=[.515, 1.70, .579], hi=[.545, 1.93, .94]),
    dict(name='side_rail_r', lo=[-.545, 1.70, .579], hi=[-.515, 1.93, .94]),
]
SKIRT_PIN_TO = {'calf_l': 'thigh_l', 'calf_r': 'thigh_r', 'foot_l': 'thigh_l', 'foot_r': 'thigh_r',
                'ball_l': 'thigh_l', 'ball_r': 'thigh_r'}


def sha(b): return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- the seated driver
def seated():
    doc, buf, body_sha = H.load(APP / BODY)
    local = H.pose(doc, buf)
    glob, _ = H.matrices(doc, local)
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
        key = node['name'].split('anonymous_working_driver_1904_')[-1].rsplit('_lod', 1)[0]
        meshes[key] = dict(posed=posed, faces=ix, joints=j, weights=w)
    bones = {doc['nodes'][i]['name']: glob[i][:3, 3] for i in skin['joints']}
    return dict(sha=body_sha, joints=joints, joint_m=joint_m, ibm=ibm, meshes=meshes, bones=bones)


def weld(P, F):
    _, idx, inv = np.unique(np.round(P * 1e5).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    inv = inv.ravel()
    return P[idx], inv[F], idx, inv


def vertex_normals(P, F):
    n = np.zeros_like(P)
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    for k in range(3): np.add.at(n, F[:, k], fn)
    return n / (np.linalg.norm(n, axis=1)[:, None] + 1e-12)


def neighbours(n, F):
    e = np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]
    e = np.unique(np.sort(e, axis=1), axis=0)
    return e


def laplacian(P, E, n):
    acc = np.zeros_like(P); cnt = np.zeros(n)
    np.add.at(acc, E[:, 0], P[E[:, 1]]); np.add.at(acc, E[:, 1], P[E[:, 0]])
    np.add.at(cnt, E[:, 0], 1); np.add.at(cnt, E[:, 1], 1)
    return acc / np.maximum(cnt, 1)[:, None] - P


class Collider:
    """What the coat may not pass through: the seated body and garments as a
    point-normal surface, and the driving box as solid blocks."""
    def __init__(self, parts, boxes=BOXES, reach=.07):
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


# ---------------------------------------------------------------- the coat's body
def coat_body(S, col):
    shirt = S['meshes']['shirt_0']
    W, G, idx, inv = weld(shirt['posed'], shirt['faces'])
    joints = shirt['joints'][idx]; weights = shirt['weights'][idx]
    name = S['joints']
    dom = np.array([name[j[np.argmax(w)]] for j, w in zip(joints, weights)])
    sleeve = np.array([d.startswith(('upperarm', 'lowerarm', 'hand')) for d in dom])
    lower_arm = np.array([d.startswith(('lowerarm', 'hand')) for d in dom])
    N = vertex_normals(W, G)
    neck_base = 2.42
    loft = np.where(sleeve, PARAMS['sleeve_loft_m'], PARAMS['coat_loft_m'])
    # The cuff eases out over the last 12 cm of the forearm.
    hand = {'l': S['bones']['hand_l'], 'r': S['bones']['hand_r']}
    to_hand = np.minimum(np.linalg.norm(W - hand['l'], axis=1), np.linalg.norm(W - hand['r'], axis=1))
    loft = loft + np.where(lower_arm, PARAMS['sleeve_cuff_flare_m'] * np.clip(1 - (to_hand - .05) / .12, 0, 1), 0)
    collar = W[:, 1] > neck_base
    loft = np.where(collar, PARAMS['collar_loft_m'] + (W[:, 1] - neck_base) * PARAMS['collar_flare'], loft)
    X = W + N * loft[:, None]
    E = neighbours(len(X), G)
    boundary = boundary_vertices(G)
    for _ in range(PARAMS['smooth_iterations']):
        for f in (.5, -.53):              # Taubin: smooth without shrinking
            L = laplacian(X, E, len(X)); L[boundary] *= .35
            X = X + f * L
        col.push(X, PARAMS['clearance_m'])
    for _ in range(4): col.push(X, PARAMS['clearance_m'])
    return dict(posed=X, faces=G, joints=joints, weights=weights, shirt_rows=idx)


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


# ---------------------------------------------------------------- draped cloth
def drape(top, centre, rows, row_m, fullness, col, lift=.25, open_front=True, bend_h=.12):
    """Hang a cloth from `top` (C x 3, ordered round `centre`, open at the front)
    and let it fall. Returns (R x C x 3) positions and the triangle grid."""
    C = len(top); R = rows
    out = top - centre; out[:, 1] = 0; out /= np.linalg.norm(out, axis=1)[:, None]
    s = np.arange(R) * row_m
    X = top[None] + out[None] * (s[:, None, None] * .92) + np.array([0, 1, 0]) * (s[:, None, None] * lift)
    prev = X.copy()
    top_len = np.linalg.norm(np.diff(top, axis=0), axis=1)              # (C-1)
    grow = 1 + (fullness - 1) * (s / s[-1])
    Lh = top_len[None] * grow[:, None]                                   # (R, C-1)
    Lv = row_m
    inv_mass = np.ones((R, C)); inv_mass[0] = 0
    g = np.array([0, -9.81, 0]) * PARAMS['drape_dt_s'] ** 2
    for step in range(PARAMS['drape_steps']):
        vel = (X - prev) * .985
        prev = X.copy()
        X = X + vel + g * inv_mass[..., None]
        for _ in range(PARAMS['drape_iterations']):
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
            X = X + 1.5 * D / np.maximum(K, 1)[..., None] * inv_mass[..., None]
        flat = X.reshape(-1, 3)
        hit = col.push(flat, PARAMS['clearance_m'])
        X = flat.reshape(R, C, 3)
        hp = hit.reshape(R, C)
        prev[hp] = X[hp] - (X[hp] - prev[hp]) * .25               # contact friction
        X[0] = top; prev[0] = top
    for _ in range(PARAMS['drape_relax_passes']):
        for f in (.5, -.53):
            L = np.zeros_like(X); n = np.zeros((R, C, 1))
            L[1:] += X[:-1]; n[1:] += 1; L[:-1] += X[1:]; n[:-1] += 1
            L[:, 1:] += X[:, :-1]; n[:, 1:] += 1; L[:, :-1] += X[:, 1:]; n[:, :-1] += 1
            X = X + f * (L / n - X) * inv_mass[..., None]
        flat = X.reshape(-1, 3); col.push(flat, PARAMS['clearance_m']); X = flat.reshape(R, C, 3)
    F = []
    for i in range(R - 1):
        for j in range(C - 1):
            a, b, c, d = i * C + j, i * C + j + 1, (i + 1) * C + j, (i + 1) * C + j + 1
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


# ---------------------------------------------------------------- the hat
def top_hat(S):
    hair = S['meshes']['short04_hair']['posed']; body = S['meshes']['body_0']['posed']
    head = np.r_[hair, body[body[:, 1] > 2.6]]
    base_y = 2.650
    band = head[np.abs(head[:, 1] - base_y) < .012]
    cx, cz = (band[:, 0].max() + band[:, 0].min()) / 2, (band[:, 2].max() + band[:, 2].min()) / 2
    rx = (band[:, 0].max() - band[:, 0].min()) / 2 + PARAMS['hat_ease_m']
    rz = (band[:, 2].max() - band[:, 2].min()) / 2 + PARAMS['hat_ease_m']
    seg = 40; th = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    ring = lambda sx, sz, y: np.c_[cx + sx * np.sin(th), np.full(seg, y), cz + sz * np.cos(th)]
    H_ = PARAMS['hat_crown_height_m']
    # Crown: a slight waist a third of the way up and a fuller top, as a silk hat's is.
    levels = [0, .1, .33, .66, .9, 1.0]; flare = [1.0, .985, .97, .985, 1.02, 1.025]
    crown = [ring(rx * f, rz * f, base_y + H_ * t) for t, f in zip(levels, flare)]
    side = np.abs(np.sin(th)); fore = np.abs(np.cos(th))
    bw = PARAMS['hat_brim_side_m'] * side + PARAMS['hat_brim_fore_m'] * fore
    curl = PARAMS['hat_brim_curl_m'] * side ** 2
    def brim(off, dy, k):
        return np.c_[cx + (rx + off * k) * np.sin(th), np.broadcast_to(base_y + dy, th.shape), cz + (rz + off * k) * np.cos(th)]
    brim_mid = brim(bw * .6, curl * .3 - .002, 1)
    brim_out = brim(bw, curl, 1)
    brim_out_lo = brim_out - [0, .005, 0]
    brim_mid_lo = brim(bw * .6, curl * .3 - .007, 1)
    under = brim(0 * bw, -.007, 1)
    rings_hat = [under, brim_mid_lo, brim_out_lo, brim_out, brim_mid] + crown
    V = np.concatenate(rings_hat)
    F = []
    for r in range(len(rings_hat) - 1):
        for j in range(seg):
            a, b = r * seg + j, r * seg + (j + 1) % seg
            c, d = a + seg, b + seg
            F += [[a, b, c], [b, d, c]]
    top_c = len(V); V = np.r_[V, [[cx, base_y + H_ * 1.0, cz]]]
    t0 = (len(rings_hat) - 1) * seg
    for j in range(seg): F.append([t0 + j, t0 + (j + 1) % seg, top_c])
    F = np.array(F)
    # Orient outward: the crown's faces must face away from its axis.
    V, F = orient_out(V, F, np.array([cx, base_y + H_ * .5, cz]))
    band_lo, band_hi = base_y + .002, base_y + .040
    bring = [ring(rx * 1.008, rz * 1.008, band_lo), ring(rx * 1.0035, rz * 1.0035, band_hi)]
    BV = np.concatenate(bring); BF = []
    for j in range(seg):
        a, b = j, (j + 1) % seg; BF += [[a, b, a + seg], [b, b + seg, a + seg]]
    BV, BF = orient_out(BV, np.array(BF), np.array([cx, base_y + .02, cz]))
    return dict(hat=(V, F), band=(BV, BF), fit=dict(base_y_m=base_y, centre_xz_m=[cx, cz], inner_radii_m=[rx, rz]))


def orient_out(V, F, centre):
    c = V[F].mean(1); n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    flip = np.einsum('ij,ij->i', n, c - centre) < 0
    F = F.copy(); F[flip] = F[flip][:, [0, 2, 1]]
    return V, F


# ---------------------------------------------------------------- buttons
def buttons(coat):
    X = coat['posed']; N = vertex_normals(X, coat['faces'])
    out_v, out_f = [], []
    r = PARAMS['button_radius_m']; seg = 10
    th = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    for side in (-1, 1):
        for y in np.linspace(2.06, 2.27, PARAMS['buttons_per_row']):
            x = side * PARAMS['button_row_half_spacing_m']
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
    V = np.array(sum(out_v, [])); F = np.concatenate(out_f)
    return V, F


# ---------------------------------------------------------------- skinning
def bind(S, posed, joints, weights):
    """Unpose positions through the seated pose's linear-blend matrices to bind space."""
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


# ---------------------------------------------------------------- build
def build():
    S = seated()
    body_parts = [(S['meshes'][k]['posed'], S['meshes'][k]['faces']) for k in ('body_0', 'trousers_0', 'closed_shoes', 'waistcoat_0', 'shirt_0')]
    col = Collider(body_parts)
    coat = coat_body(S, col)
    # The skirt hangs from the coat's hem; the cape from round the collar's foot.
    loops = boundary_loops(coat['faces'])
    hem = min(loops, key=lambda l: coat['posed'][l, 1].mean())
    centre = coat['posed'][hem].mean(0)
    skirt_top = ring_from_loop(coat['posed'], hem, centre, 97, inset=.006, rise=.03)
    coat_col = Collider(body_parts + [(coat['posed'], coat['faces'])])
    skirt, skirt_f = drape(skirt_top, centre, int(round(PARAMS['skirt_length_m'] / PARAMS['skirt_row_m'])) + 1,
                           PARAMS['skirt_row_m'], PARAMS['skirt_hem_fullness'], col)
    X = coat['posed']
    neck = S['bones']['neck_01']
    band = np.where((X[:, 1] > 2.395) & (X[:, 1] < 2.45) & (np.hypot(X[:, 0] - neck[0], X[:, 2] - neck[2]) < .105))[0]
    neck_c = X[band].mean(0)
    ang = np.arctan2(X[band, 0] - neck_c[0], X[band, 2] - neck_c[2])
    cape_ring = []
    for a in np.r_[np.linspace(.04, np.pi, 37)[:-1], np.linspace(-np.pi, -.04, 37)]:
        dirn = np.array([math.sin(a), 0, math.cos(a)])
        cand = band[np.abs(((ang - a + np.pi) % (2 * np.pi)) - np.pi) < .5]
        far = cand[np.argmax((X[cand] - neck_c) @ dirn)]
        cape_ring.append(X[far] + dirn * .006 + [0, .004, 0])
    cape_ring = np.array(cape_ring)
    cape, cape_f = drape(cape_ring, neck_c, int(round(PARAMS['cape_length_m'] / PARAMS['cape_row_m'])) + 1,
                         PARAMS['cape_row_m'], PARAMS['cape_hem_fullness'], coat_col, lift=.05, bend_h=.3)
    hat = top_hat(S)
    bv, bf = buttons(coat)
    parts = []
    def add(name, material, posed, faces, joints, weights):
        b = bind(S, posed, joints, weights)
        n = vertex_normals(posed, faces)
        M = np.einsum('vn,vnij->vij', weights, S['joint_m'][joints])[:, :3, :3]
        nb = np.einsum('vij,vj->vi', np.linalg.inv(M), n)        # rigid-ish: inverse rotation
        nb /= np.linalg.norm(nb, axis=1)[:, None] + 1e-12
        parts.append(dict(name=name, material=material, bind=b, normal=nb, joints=joints, weights=weights, faces=faces, posed=posed))
    add('box_coat_body', 'garment_outer__box_coat_wool', coat['posed'], coat['faces'], *[coat['joints'], coat['weights']])
    sk = skirt.reshape(-1, 3)
    add('box_coat_skirt', 'garment_outer__box_coat_wool', sk, skirt_f,
        *nearest_weights(S, sk, ['trousers_0', 'body_0'], remap=SKIRT_PIN_TO))
    cp = cape.reshape(-1, 3)
    add('box_coat_cape', 'garment_outer__box_coat_wool', cp, cape_f, *nearest_weights(S, cp, ['shirt_0']))
    for name, mat, (V, F) in [('top_hat', 'headwear__silk_top_hat', hat['hat']), ('top_hat_band', 'headwear__hat_band_grosgrain', hat['band'])]:
        add(name, mat, V, F, *rigid(S, len(V), 'head'))
    add('livery_buttons', 'accessory__brass_livery_buttons', bv, bf, *nearest_weights(S, bv, ['shirt_0'], k=3))
    return S, merge_by_material(parts), hat['fit']


def merge_by_material(parts):
    """One mesh (one draw) per material: the coat's body, skirt and cape are one cloth."""
    out = {}
    for p in parts:
        q = out.get(p['material'])
        if q is None: out[p['material']] = dict(p, name=p['name'], faces=p['faces'].copy()); continue
        off = len(q['bind'])
        for k in ('bind', 'normal', 'joints', 'weights', 'posed'): q[k] = np.concatenate([q[k], p[k]])
        q['faces'] = np.concatenate([q['faces'], p['faces'] + off]); q['name'] += '+' + p['name']
    return list(out.values())


def b64(a, dtype): return base64.b64encode(np.ascontiguousarray(a, dtype=dtype).tobytes()).decode()


def document(S, parts, fit):
    used = sorted({int(j) for p in parts for j, w in zip(p['joints'].ravel(), p['weights'].ravel()) if w > 0})
    remap = {j: i for i, j in enumerate(used)}
    out_parts = []
    for p in parts:
        J = np.vectorize(lambda j: remap.get(int(j), 0))(p['joints']); J[p['weights'] == 0] = 0
        out_parts.append(dict(name=p['name'], material=p['material'], vertex_count=int(len(p['bind'])),
                              triangle_count=int(len(p['faces'])),
                              position=b64(np.round(p['bind'], 6), '<f4'), normal=b64(np.round(p['normal'], 5), '<f4'),
                              joints=b64(J, '<u1'), weights=b64(np.round(p['weights'], 5), '<f4'),
                              index=b64(p['faces'].ravel(), '<u2' if len(p['bind']) < 65536 else '<u4')))
    return dict(
        schema=SCHEMA, ticket='T-3398', asset_id='anonymous_working_driver_1904', clip_posed='sit_drive',
        body_master=BODY, body_master_sha256=S['sha'],
        vehicle=VEHICLE, vehicle_glb_sha256=sha((APP / VEHICLE).read_bytes()),
        grade='reconstructed', liberty='L-driven-town-circuits-2804', license='CC0-1.0',
        producer='tools/human_driver_livery_1904.py',
        basis=('A private brougham coachman of about 1904 dressed for the box: a long double-breasted box coat '
               'with a shoulder cape and turned-up collar, brass livery buttons and a silk top hat. Cut, length, '
               'colour and fit are reconstructed authoring choices; no surviving garment, photograph or record '
               'of what Hans Johnson wore is claimed.'),
        parameters=PARAMS, materials=MATERIALS, recolor_body_materials=RECOLOR, vehicle_box_colliders=BOXES, hat_fit=fit,
        joints=[S['joints'][j] for j in used],
        inverse_bind_matrices=[np.round(S['ibm'][j].T.ravel(), 7).tolist() for j in used],
        # A few vertices of each part where the producer posed them (sit_drive), so the
        # renderer's own skinning can be held to them (tools/test_driver_livery.mjs).
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


def check():
    """The committed file against its inputs and the seated body, without re-draping
    (the drape is a long float integration and is not promised byte-identical across
    machines): same body master and vehicle, sane skin data, and, posed again, no coat
    point inside the body, the garments it covers or the driving box."""
    doc_ = json.loads((APP / OUT).read_text())
    S = seated()
    errors = []
    if doc_['schema'] != SCHEMA: errors.append('schema')
    if doc_['body_master_sha256'] != S['sha']: errors.append('the body master changed since the livery was draped: rerun the producer')
    if doc_['vehicle_glb_sha256'] != sha((APP / VEHICLE).read_bytes()): errors.append('the brougham changed since the livery was draped: rerun the producer')
    names = doc_['joints']
    if any(n not in S['joints'] for n in names): errors.append('a livery joint is not on the driver')
    for n, m in zip(names, doc_['inverse_bind_matrices']):
        if np.abs(np.array(m) - S['ibm'][S['joints'].index(n)].T.ravel()).max() > 1e-5: errors.append(f'inverse bind of {n} differs')
    if set(p['material'] for p in doc_['parts']) - set(doc_['materials']): errors.append('a part names an undeclared material')
    body_parts = [(S['meshes'][k]['posed'], S['meshes'][k]['faces']) for k in ('body_0', 'trousers_0', 'closed_shoes', 'waistcoat_0', 'shirt_0')]
    col = Collider(body_parts, reach=.05)
    worst = {}
    for p in decode(doc_):
        J = np.array([S['joints'].index(names[j]) for j in p['joints'].ravel()]).reshape(-1, 4)
        if not np.all(np.isfinite(p['bind'])) or np.abs(p['weights'].sum(1) - 1).max() > 1e-3: errors.append(f'{p["name"]}: bad skin data')
        if p['faces'].max() >= len(p['bind']): errors.append(f'{p["name"]}: index out of range')
        M = np.einsum('vn,vnij->vij', p['weights'], S['joint_m'][J])
        X = np.einsum('vij,vj->vi', M, np.c_[p['bind'], np.ones(len(p['bind']))])[:, :3]
        Y = X.copy(); col.push(Y, 0.0)
        worst[p['name']] = float(np.linalg.norm(Y - X, axis=1).max())
        # 8 mm: the drape keeps 8 mm off a point-normal surface; a cloth squeezed
        # between the thighs may give some of that back, never more.
        if worst[p['name']] > .008: errors.append(f'{p["name"]}: {worst[p["name"]] * 1000:.1f} mm inside the body or the box')
    if errors:
        print('driver livery: FAIL\n  ' + '\n  '.join(errors)); sys.exit(1)
    print('driver livery: the committed coat, cape and hat match their body and box, skin finite and normalised, '
          'nothing inside the seated body or the box (worst ' + ', '.join(f'{k} {v * 1000:.1f} mm' for k, v in worst.items()) + '): PASS')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--check', action='store_true'); args = ap.parse_args()
    if args.check: check()
    else:
        S, parts, fit = build()
        text = json.dumps(document(S, parts, fit), separators=(',', ':')) + '\n'
        (APP / OUT).write_text(text)
        print(json.dumps({p['name']: [len(p['bind']), len(p['faces'])] for p in parts}), f'{len(text) / 1e6:.2f} MB')
