#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""A face traced onto a side view of its stand-in (T-3553).

    python3 tools/trace_portrait_profile.py PERSON RENDER.png DUMP.json [--dry OUT.jpg]

The owner, 2026-11-13, sent turnaround sheets of the Greys' stand-ins ("These might help"):
each head from the front, both sides and behind. One near-frontal portrait cannot measure how
far a nose, lips or chin stand out (tools/fit_portrait_face.py leaves depth to the body and the
reader); a side view shows exactly that, as the line of the face against the sky. This tool
carries the render's line onto the picture's, as tools/trace_portrait_face.py carries the
front view's points.

The picture's readings live in the portrait record's `trace.profile` (sheet pixels of the copy
named in its `scan`): the face's silhouette from the forehead to the neck (`silhouette_px`,
read off the sheet's white ground), the visible eye's corners and lids and the lips' meeting
(MediaPipe Face Landmarker, `marks_px`), the tragus (`tragus_px`, read by eye), the render turn
that matches the sheet's (`render_yaw_deg`) and the skin vertex drawn at the tragus
(`tragus_kit_vertex`). RENDER.png and DUMP.json are a render of
the person as the renderer draws them now, turned to `render_yaw_deg` (tools/
human_variation_lineup.html, keys=<person>, dress=1, aim=head, dist=1.1, look=0.02, at
device pixel ratio 2) and that page's `window.__vertexDump()` beside it. A pass:

  1. The picture is laid on the render: turned by the line from the eye to the tragus, scaled
     by the height from the eye to the lips' meeting (heights the front view's trace has already
     matched, and which a turn of the head does not foreshorten), placed on the eye, and slid
     sideways so its forehead lies on the render's (the forehead is the reference, as a
     portraitist lays one profile on another).
  2. Each point of the render's silhouette from the brow to the chin's point (`points`: `chin`;
     or, `nose`, from the bridge below the nasion to under the nose, where a beard hides the
     rest and the nasion is held with the forehead; or, `neck`, on under the jaw to the neck,
     from a render with the clothes hidden, hide=^headwear|^garment) moves to the nearest point of
     the picture's; the skin vertex drawn there takes that move, read into the head's own
     frame. The forehead's silhouette is held still, and a side view sees no sideways move.
  3. tools/trace_portrait_face.py's profile pass spreads the moves over the face (each shared
     with the vertex's mirror, the eyes held) and adds a damped share to the person's trace.

Repeat with fresh renders until the mean move is about a millimetre, alternating with front-view
passes so the two views agree. Reconstructed, like the fit (L-human-variation-3412).
"""
import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fit_portrait_face as fpf  # noqa: E402
import trace_portrait_face as tpf  # noqa: E402

EYES = ([33, 133, 159, 145, 160, 144], [263, 362, 386, 374, 387, 373])
REACH_PX = 90        # a render point further than this from the picture's line is not moved
PICK_PX = 4.0        # a silhouette point's skin vertex is drawn within this of it


def camera(dump):
    h = np.array(dump['head'])
    cam = h + np.array([0.0, dump['look'] + 0.01, dump['dist']])
    tgt = h + np.array([0.0, dump['look'], 0.0])
    f = cam - tgt
    f /= np.linalg.norm(f)
    r = np.cross([0.0, 1.0, 0.0], f)
    r /= np.linalg.norm(r)
    u = np.cross(f, r)
    W, H = dump['size']
    focal = (H / 2) / np.tan(np.radians(dump['fov'] / 2))
    return cam, r, u, f, W, H, focal


def project(P, dump):
    cam, r, u, f, W, H, focal = camera(dump)
    X = P - cam
    zc = -(X @ f)
    return np.stack([W / 2 + (X @ r) / zc * focal, H / 2 - (X @ u) / zc * focal], 1), zc


def contour(mask):
    import cv2
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return max(cs, key=len)[:, 0, :].astype(float)


def render_mask(path):
    from PIL import Image
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)
    return a, np.abs(a - np.array([0x8a, 0x86, 0x80])).sum(2) > 18   # the lineup's ground


def weighted_similarity(a, b, w):
    w = np.asarray(w, float)[:, None]
    ma, mb = (a * w).sum(0) / w.sum(), (b * w).sum(0) / w.sum()
    A, B = (a - ma) * np.sqrt(w), (b - mb) * np.sqrt(w)
    U, _, Vt = np.linalg.svd(A.T @ B)
    return (U @ Vt).T, ma, mb


def read_pass(person, render_png, dump_path):
    portrait = json.loads((fpf.PORTRAITS / f'{person}.json').read_text())
    prof = portrait['trace']['profile']
    asset = portrait['base_body']
    dump = json.loads(pathlib.Path(dump_path).read_text())
    P = np.array(dump['pos'], float).reshape(-1, 3)
    kit_of = np.array(dump['map'], int)
    xy, zc = project(P, dump)
    first = {}
    for i, k in enumerate(kit_of):
        first.setdefault(int(k), i)
    kidx = fpf.kit_index()
    table = json.loads(tpf.TABLE.read_text())['bodies'][asset]
    at = {int(n[3:]): first[kidx[p['vertex']]] for n, p in table['points'].items() if kidx.get(p['vertex']) in first}
    mk = {int(k): np.array(v, float) for k, v in prof['marks_px'].items()}

    # 1. Lay the picture on the render.
    eye = min(EYES, key=lambda e: np.mean([zc[at[i]] for i in e if i in at]))   # the nearer eye
    use = [i for i in eye if i in at and i in mk]
    tr_r = xy[first[prof['tragus_kit_vertex']]]
    A = np.vstack([[mk[i] for i in use], [prof['tragus_px']]])
    B = np.vstack([[xy[at[i]] for i in use], [tr_r]])
    R, ma, mb = weighted_similarity(A, B, [1.0] * len(use) + [float(len(use))])
    ph = (mk[13] + mk[14]) / 2 - np.mean([mk[i] for i in use[:2]], 0)
    rh = (xy[at[13]] + xy[at[14]]) / 2 - np.mean([xy[at[i]] for i in use[:2]], 0)
    s = np.linalg.norm(rh) / np.linalg.norm(ph)
    pic = (np.asarray(prof['silhouette_px'], float) - ma) @ R.T * s + mb

    # 2. The render's silhouette, its moves, and the skin vertices drawn on it.
    img, mask = render_mask(render_png)
    left = xy[at[4]][0] < tr_r[0]
    sgn = 1 if left else -1
    ny = xy[at[168]][1]
    F = xy[at[17]][1] + (xy[at[17]][1] - ny) * 0.4 - ny          # nasion to about the chin
    c = contour(mask)
    c = c[((c[:, 0] < tr_r[0]) if left else (c[:, 0] > tr_r[0])) & (c[:, 1] > ny - F * 0.6) & (c[:, 1] < ny + F * 1.5)]
    if (c[:, 0].min() < 3) or (c[:, 0].max() > img.shape[1] - 4):
        sys.exit('the face runs off the render: render it from further away')
    skin = np.array([not (img[int(p[1]), int(p[0] + sgn * 6)].min() > 175) for p in c])   # not the collar
    c = c[skin]
    band = lambda a, lo, hi: a[(a[:, 1] > lo) & (a[:, 1] < hi)]                # noqa: E731
    # The forehead registration: slide the picture sideways until its forehead lies on the
    # render's (the render's forehead is held still by every pass, so this does not drift).
    rows = np.arange(ny - F * 0.45, ny - F * 0.18, 4.0)
    edge = lambda a, y: (lambda r: (r[:, 0].min() if left else r[:, 0].max()) if len(r) else np.nan)(a[np.abs(a[:, 1] - y) < 3])  # noqa: E731
    shift = float(np.nanmedian([edge(c, y) - edge(pic, y) for y in rows]))
    pic = pic + np.array([shift, 0.0])
    near_chin = band(c, ny + F * 0.7, ny + F * 1.3)
    if prof.get('points', 'chin') == 'nose':
        bottom = xy[at[2]][1] + F * 0.03
    elif prof['points'] == 'neck':
        bottom = ny + F * prof.get('neck_to', 1.35)            # on under the jaw to the neck
    else:
        bottom = near_chin[np.argmin(sgn * near_chin[:, 0])][1] + F * 0.06
    if prof.get('points', 'chin') == 'nose':     # the nose alone: the forehead and the nasion held
        traced, held = band(c, ny + F * 0.12, bottom), band(c, ny - F * 0.5, ny + F * 0.02)
    else:
        traced, held = band(c, ny - F * 0.12, bottom), band(c, ny - F * 0.5, ny - F * 0.2)
    from scipy.spatial import cKDTree
    dist, j = cKDTree(pic).query(traced)
    moves2d = pic[j] - traced
    ok = dist < REACH_PX
    head = np.where(P[:, 1] > dump['head'][1] - 0.12)[0]
    kv = cKDTree(xy[head])
    picks = []
    for p, d in list(zip(traced[ok][::3], moves2d[ok][::3])) + [(p, np.zeros(2)) for p in held[::3]]:
        nb = kv.query_ball_point(p, PICK_PX)
        if nb:
            picks.append((head[min(nb, key=lambda k: zc[head[k]])], d))
    V = np.array([i for i, _ in picks])
    D2 = np.array([d for _, d in picks])
    _, r, u, _, _, _, focal = camera(dump)
    Dw = (D2[:, :1] * r[None] - D2[:, 1:] * u[None]) * (zc[V] / focal)[:, None]
    rest = fpf.body_rest(asset)
    Wp, Rp = P[head], rest[kit_of[head]]
    U_, _, Vt = np.linalg.svd((Rp - Rp.mean(0)).T @ (Wp - Wp.mean(0)))
    Dk = Dw @ (U_ @ Vt).T                                       # world to the rest frame
    Dk[:, 0] = 0.0
    moving = np.linalg.norm(D2, axis=1) > 0
    miss = float(np.linalg.norm(Dk[moving], axis=1).mean() * 1000)
    return {'vertices': [int(k) for k in kit_of[V]], 'moves': Dk.tolist(), 'miss_mm': round(miss, 2), 'shift_px': round(shift, 1)}, (img, c, pic)


def main():
    args = sys.argv[1:]
    if len(args) not in (3, 5):
        sys.exit(__doc__)
    person, render_png, dump_path = args[:3]
    d, (img, c, pic) = read_pass(person, render_png, dump_path)
    if len(args) == 5 and args[3] == '--dry':
        from PIL import Image, ImageDraw
        im = Image.fromarray(img.astype(np.uint8))
        dr = ImageDraw.Draw(im)
        for x, y in c[::2]:
            dr.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(255, 0, 0))
        for x, y in pic[::1]:
            dr.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(0, 90, 255))
        im.save(args[4])
        print(f'{person}: mean move {d["miss_mm"]} mm over {len(d["vertices"])} silhouette vertices, forehead slid {d["shift_px"]} px (not written)')
        return
    tpf.profile_pass(person, d)


if __name__ == '__main__':
    main()
