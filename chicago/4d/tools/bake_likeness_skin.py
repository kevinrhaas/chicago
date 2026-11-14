#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""A stand-in's photographs as the skin, hair and eyes of the face fitted to them (T-3553).

    python3 tools/bake_likeness_skin.py PERSON --sheet SHEET.png          bake the person's skin
    python3 tools/bake_likeness_skin.py PERSON --sheet SHEET.png --detect MODEL.task
                                                                         read the views' points first
    python3 tools/bake_likeness_skin.py PERSON --sheet SHEET.png --preview OUT.jpg
                                                                         and a strip of turns to look at
    python3 tools/bake_likeness_skin.py --check                          every record against its files

The owner, 2026-11-13, of William and Sarah Grey's stand-ins: "take a swing at doing another
photo match and see if you can tune both him and her to perfect, add what is needed to the face
model to make it work ... i want them photographic matched". A face fitted to a stand-in's
pictures (tools/fit_portrait_face.py) lay within about 2 mm of them at four hundred points and
still read as somebody else, because its skin was every body's skin: one MakeHuman colour map,
shaded brows, strand-card hair, flat-coloured eyes opened wider than the pictures'. What makes a
picture of a face that face is its surface. So the stand-in's own pictures are laid on the
fitted head:

  - the record data/humans/variation/skins/<PERSON>.json names the owner's turnaround sheet (four
    pictures of the stand-in's head on one sheet: front, the two sides, the back; kept in
    kevinrhaas/chicago-evidence, not in this repository) and, for each view, its quadrant and
    MediaPipe Face Landmarker's points on it (`--detect`);
  - each view gets its own weak-perspective camera, as the fit's are: the front from the points
    on the skin vertices the correspondence table names (data/humans/variation/
    mediapipe_hm08_landmarks.json; `camera: "upper_face"` uses only the points above the nose's
    base, for a front view that smiles), a side turned as the fit turned its own side view (the
    record's `turn_deg` where the fit has none) and placed by its near-side points and the
    face's line against the sheet's white ground, the back from the hair's top and the collar;
  - the lids come first (`rest_lids`): the fitted face's eyes stand wider open than the
    pictures', so the blink's own shape (renderers/web/js/human-skin.js shapeBlink, read here by
    `blink_shape`) is taken as far as closes them to the front picture's opening, between the
    lids' edges; the cameras are found again on that face, and `texture.lids.rest` tells the
    renderer to rest the lids the same;
  - the front view is then warped a little (a thin-plate spline through the points), so the
    picture's own lips, lids, nostrils and brows land on the mesh's;
  - the hair (`hair_shown`, `grow`): each skin vertex is read as hair or skin by the pictures'
    colour at it (the face's own skin tone against the tones outside the bare head's outline),
    and where it is hair the skin is moved out, along the line from the head's middle, to the
    pictures' outline: in each view the line's length inside the picture's head less its length
    inside the bare head's own outline, the views weighed by how squarely they see that line,
    never past any view's outline, off the face and clear of the ears. The pictures are laid on
    that grown head;
  - every texel of the head, eye sockets and neck in the body's own UV layout takes the view that sees
    it best: the front inside the outer corners of the eyes (and wherever the hair stands out
    toward it), a side beyond them, the back behind the ears; what no view sees (the crown,
    behind an ear) is filled from around it. Clothing (the collar and all below it) is left
    out, and earrings are painted over from the skin beside them;
  - each iris (`read_eyes`) is read from the front picture as rings about its centre and drawn
    whole, with the colour of the whites beside it;
  - the result is one JPEG, assets/humans/web/likeness/<PERSON>_skin.jpg: `RECTS` place the
    head, eye sockets and neck on it, and its spare column holds three blocks of the tool's own.
    The mask (`MASK`, a quarter the sheet's size): green where the sheet covers, red how far the
    hair stands out as a share of `texture.grow.reach_m`, blue where the pictures show hair.
    Under it (`SHAPE_PX`) which way the grown surface faces, so it is lit as its own shape. Under
    that (`EYES`) the two irises. renderers/web/js/human-skin.js lays the sheet over the body's
    skin where the mask covers, moves the skin out by the red, lights the blue as hair, and
    gives the eyes their irises and whites. The record also keeps `tint`: the pictures' cheek
    tone over the body's own map's there, which the rest of the body's skin (the neck below the
    collar line, the hands) is multiplied by, so the figure is one person's skin from the face
    down.

What this is and is not. The pictures are the owner's stand-ins (source records
owner_grey_likeness_*_2026, tier 5, rights cleared by the owner's instruction for this project's
use and derivation): no photograph of William or Sarah Grey is known. The skin, hair and eyes
are therefore a reconstructed likeness, as the fitted face is (docs/LIBERTIES.md,
L-grey-photograph-skin-3553), and the person's card says STAND-IN. Nothing here is evidence of
how either looked.

`--check` holds each record to its files: the texture's SHA-256, the layout constants, what the
bake recorded of the hair, lids and eyes, and the fitted values the bake was made on (a refit
means a rebake). It needs no picture.
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fit_portrait_face as F  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKINS = ROOT / 'data/humans/variation/skins'
OUT_DIR = ROOT / 'assets/humans/web/likeness'
FORMAT = 'chicago4d_human_likeness_skin_v1'

# Where the head's pieces of the body's UV layout (glTF: v down) are drawn on the sheet, pixels.
# The hm08 layout keeps the head (its ears on it), the two eye sockets and the top of the neck
# as separate islands.
TEXTURE_PX = (768, 1024)
RECTS = (
    {'name': 'head', 'uv': (0.635, 0.175, 1.0, 0.86), 'px': (0, 0, 512, 1024)},
    {'name': 'sockets', 'uv': (0.005, 0.36, 0.158, 0.46), 'px': (520, 0, 768, 162)},
    {'name': 'neck', 'uv': (0.24, 0.02, 0.52, 0.14), 'px': (520, 170, 768, 276)},
)
MASK = {'px': (528, 292), 'scale': 0.25}     # the coverage mask, a quarter the sheet's size, at this corner
SHAPE_PX = (528, 566)                         # ...and under it, as large, which way the grown hair's surface faces
JPEG_QUALITY = 88
HEAD_DROP_M = 0.36                            # the triangles within this of the crown are the head and neck
GROW_STEP_M = 0.001                           # the step the hair's outline is felt for, out from the skin
GROW_FEEL_M = 0.25                            # ...and how far out it is felt for
HAIR_SKIN_SPREAD = np.array([10.0, 4.0, 4.0])   # the least spread (L*, a*, b*) the skin's colour is given
HAIR_COLOURS = 4                              # the hair's colours are read as this many
HAIR_GROWS = (0.35, 0.65)                     # hair stands out from the skin where the pictures read this much hair
LID_PAIRS = ((159, 145), (386, 374))          # MediaPipe: the middle of each eye's upper and lower lid
LID_EDGE_M = (0.0025, 0.012, 0.02)            # a lid's edge at its middle: the open boundary within this of it (across, up, back)
LID_REST_MOST = 0.5                           # the lids never rest more than half shut
EYES = {'px': (528, 838), 'size': 96}         # each eye's own iris, drawn from the front picture: two squares side by side
EYE_CHROMA = (0.5, 0.8)                       # an iris shows where the picture has under this share of the cheek's chroma; the white, this
EYE_ABOVE = 0.15                              # ...read from this share of its radius above its centre, and all below
EYE_WHITE_COLOUR = 0.5                        # the whites keep this share of the colour read for them
EYE_DISC = 0.455                              # the iris fills this much of its square, centre to rim (the eye meshes' own UVs)
EYE_RIMS = (                                  # MediaPipe: each eye's opening, its iris's middle and the iris's ring; the body's left first
    ((263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466), 473, (474, 475, 476, 477)),
    ((33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246), 468, (469, 470, 471, 472)),
)
LIPS = (61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185)   # MediaPipe's outer lip ring
NECK_KEEP_M = (-0.004, 0.012)                 # the head is whole from here above the chin's point


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def values_sha(person):
    fit = json.loads((F.FITS / f'{person}.json').read_text())
    return hashlib.sha256(json.dumps(fit['values'], sort_keys=True).encode()).hexdigest()


# ---------------------------------------------------------------- the fitted head

def glb_attribute(asset, name):
    import struct
    blob = (ROOT / 'assets/humans' / f'{asset}.lod0.glb').read_bytes()
    n = struct.unpack('<I', blob[12:16])[0]
    gltf, binary = json.loads(blob[20:20 + n]), blob[28 + n:]
    mesh = next(m for m in gltf['meshes'] if '_body_' in m['name'])
    acc = gltf['accessors'][mesh['primitives'][0]['attributes'][name]]
    view = gltf['bufferViews'][acc['bufferView']]
    off = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    k = {'VEC3': 3, 'VEC2': 2}[acc['type']]
    return np.frombuffer(binary, dtype='<f4', count=acc['count'] * k, offset=off).reshape(-1, k).astype(float)


def base_map(asset):
    """The body's own skin colour map (the unoptimised export's), 0..1 sRGB."""
    import io
    import struct
    from PIL import Image
    blob = (ROOT / 'assets/humans' / f'{asset}.lod0.glb').read_bytes()
    n = struct.unpack('<I', blob[12:16])[0]
    gltf, binary = json.loads(blob[20:20 + n]), blob[28 + n:]
    skin = next(m for m in gltf['materials'] if m['name'] == 'skin')
    image = gltf['images'][gltf['textures'][skin['pbrMetallicRoughness']['baseColorTexture']['index']]['source']]
    view = gltf['bufferViews'][image['bufferView']]
    off = view.get('byteOffset', 0)
    return np.asarray(Image.open(io.BytesIO(binary[off:off + view['byteLength']])).convert('RGB')).astype(np.float32) / 255


def fitted_head(person):
    """The body's skin with the person's fitted face on it, in the kit's vertex order (metres)."""
    portrait = json.loads((F.PORTRAITS / f'{person}.json').read_text())
    fit = json.loads((F.FITS / f'{person}.json').read_text())
    header, refs, axes = F.load_kit()
    asset = portrait['base_body']
    rest = F.body_rest(asset)
    rows = np.arange(len(rest))
    X, _, _, held, _ = F.face_base(person, portrait, header, refs, axes, rows)
    values = dict(fit['values'])
    option = int(values.pop('head_shape.option', 0))
    for aid, v in values.items():
        if aid in held or aid not in axes:      # face_base has already put the held axes on
            continue
        X = X + F.delta_at(axes[aid], v, option, rows)
    table = json.loads(F.MP_TABLE.read_text())['bodies'][asset]
    kidx = F.kit_index()
    side = (fit.get('fit', {}).get('views') or {}).get('side_camera') or {}
    return {'X': X, 'rest': rest, 'tri': F.body_triangles(asset), 'uv': glb_attribute(asset, 'TEXCOORD_0'), 'asset': asset,
            'side_turn_deg': abs(side['yaw_deg']) if 'yaw_deg' in side else None,
            'mp': {int(k[3:]): kidx[v['vertex']] for k, v in table['points'].items()},
            'lm': {k: kidx[v] for k, v in F.landmarks().items() if isinstance(v, int)}}


# ---------------------------------------------------------------- a small rasteriser

def raster(P, z, tri, size):
    """Triangles `tri` of points P (pixels) and depths z (larger is nearer) drawn on a (W, H)
    sheet: the nearest depth, the triangle and its barycentric weights at each pixel."""
    W, H = size
    zbuf = np.full((H, W), -np.inf)
    tbuf = np.full((H, W), -1, np.int32)
    bary = np.zeros((H, W, 3), np.float32)
    A, B, C = P[tri[:, 0]], P[tri[:, 1]], P[tri[:, 2]]
    lo = np.floor(np.minimum(np.minimum(A, B), C)).astype(int)
    hi = np.ceil(np.maximum(np.maximum(A, B), C)).astype(int)
    den = (B[:, 1] - C[:, 1]) * (A[:, 0] - C[:, 0]) + (C[:, 0] - B[:, 0]) * (A[:, 1] - C[:, 1])
    for k in range(len(tri)):
        if abs(den[k]) < 1e-12:
            continue
        xa, xb, ya, yb = max(lo[k, 0], 0), min(hi[k, 0], W - 1), max(lo[k, 1], 0), min(hi[k, 1], H - 1)
        if xa > xb or ya > yb:
            continue
        xs, ys = np.meshgrid(np.arange(xa, xb + 1) + 0.5, np.arange(ya, yb + 1) + 0.5)
        w0 = ((B[k, 1] - C[k, 1]) * (xs - C[k, 0]) + (C[k, 0] - B[k, 0]) * (ys - C[k, 1])) / den[k]
        w1 = ((C[k, 1] - A[k, 1]) * (xs - C[k, 0]) + (A[k, 0] - C[k, 0]) * (ys - C[k, 1])) / den[k]
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        zz = w0 * z[tri[k, 0]] + w1 * z[tri[k, 1]] + w2 * z[tri[k, 2]]
        sub = zbuf[ya:yb + 1, xa:xb + 1]
        upd = inside & (zz > sub)
        if not upd.any():
            continue
        sub[upd] = zz[upd]
        tbuf[ya:yb + 1, xa:xb + 1][upd] = k
        bary[ya:yb + 1, xa:xb + 1][upd] = np.stack([w0, w1, w2], -1)[upd]
    return zbuf, tbuf, bary


def vertex_normals(X, tri):
    n = np.cross(X[tri[:, 1]] - X[tri[:, 0]], X[tri[:, 2]] - X[tri[:, 0]])
    N = np.zeros_like(X)
    for i in range(3):
        np.add.at(N, tri[:, i], n)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def sample(img, xy):
    """`img` (H, W, C) read bilinearly at the pixel points xy."""
    H, W = img.shape[:2]
    x = np.clip(xy[:, 0] - 0.5, 0, W - 1.001)
    y = np.clip(xy[:, 1] - 0.5, 0, H - 1.001)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


# ---------------------------------------------------------------- the pictures

def project(X, cam, centre):
    yaw, pitch, roll, s, tx, ty = cam
    Y = (X - centre) @ F.rot(yaw, pitch, roll).T
    return np.stack([tx + s * Y[:, 0], ty - s * Y[:, 1]], 1), Y[:, 2]


def solve_camera(P, ob, centre, yaws):
    from scipy.optimize import least_squares
    best = None
    for y0 in yaws:
        c = np.array([y0, 0.0, 0.0, 1.0, 0.0, 0.0])
        Q, _ = project(P, c, centre)
        c[3] = np.linalg.norm(ob.max(0) - ob.min(0)) / max(np.linalg.norm(Q.max(0) - Q.min(0)), 1e-9)
        c[4:] = ob.mean(0) - project(P, c, centre)[0].mean(0)
        r = least_squares(lambda q: (project(P, q, centre)[0] - ob).ravel(), c, x_scale='jac', loss='soft_l1', f_scale=3.0)
        if best is None or r.cost < best.cost:
            best = r
    return best.x


def figure_mask(img):
    """The figure against the sheet's white ground."""
    from scipy import ndimage
    m = (img.min(2) < 236 / 255) | ((img.max(2) - img.min(2)) > 18 / 255)
    m = ndimage.binary_opening(m, iterations=1)
    lab, n = ndimage.label(m)
    if n > 1:
        m = lab == 1 + np.argmax(ndimage.sum(m, lab, range(1, n + 1)))
    return ndimage.binary_fill_holes(m)


def bright_parts(img, fg):
    """Pale, colourless parts of the figure: a white collar, lace, an earring's metal (and a
    grey temple or a tooth, which their place tells apart)."""
    from scipy import ndimage
    mx, mn = img.max(2), img.min(2)
    b = (mx > 168 / 255) & ((mx - mn) / np.maximum(mx, 1e-3) < 0.30) & fg
    lab, n = ndimage.label(b)
    return lab, (ndimage.sum(b, lab, range(1, n + 1)) if n else np.array([]))


def diffuse_fill(img, hole, known=None):
    """`hole` pixels of img (H, W, C) filled from the known ones round them: the nearest known
    colour, then smoothed from coarse to fine."""
    from scipy import ndimage
    known = ~hole if known is None else known
    out = img.copy()
    idx = ndimage.distance_transform_edt(~known, return_distances=False, return_indices=True)
    out[hole] = img[idx[0][hole], idx[1][hole]]
    for s in (8, 4, 2, 1):
        for _ in range(12):
            blur = np.stack([ndimage.uniform_filter(out[:, :, c], 2 * s + 1) for c in range(out.shape[2])], -1)
            out[hole] = blur[hole]
    return out


def side_camera(head, T, pts, fg, turn_deg, centre, size, scale):
    """A side view's camera: its near-side points, and the face's line against the white ground
    matched by the head's own outline from that side (closest points, re-found each pass). The
    turn is the record's, read from the picture by eye, and is held: left free it settles some
    twenty degrees short of a profile, a fitted nose a little too long read as a head not quite
    side-on, which lays the back of the head and the hair in the wrong place. The scale stays
    near the front view's (one sheet, one camera distance)."""
    from scipy import ndimage
    from scipy.optimize import least_squares
    from scipy.spatial import cKDTree
    X, mp, lm = head['X'], head['mp'], head['lm']
    near = 1.0 if turn_deg < 0 else -1.0       # a face turned to the viewer's left shows the body's left side (+x)
    idx = [i for i in sorted(mp) if X[mp[i], 0] * near > 0.012]
    P, ob = X[[mp[i] for i in idx]], pts[idx]
    turn = np.radians(turn_deg)
    cam = solve_camera(P, ob, centre, [turn])
    edge = fg & ~ndimage.binary_erosion(fg)
    ey, ex = np.nonzero(edge)
    E = np.stack([ex, ey], 1).astype(float)
    hv = np.unique(T)
    ear_z = max(X[lm['ear_top_r'], 2], X[lm['ear_lobe_r'], 2])
    for _ in range(8):
        Pm, z = project(X, cam, centre)
        _, tb, _ = raster(Pm, z, T, size)
        mm = tb >= 0
        yy, xx = np.nonzero(mm & ~ndimage.binary_erosion(mm))
        d, j = cKDTree(Pm[hv]).query(np.stack([xx, yy], 1) + 0.5)
        rows = np.unique(hv[j[d < 1.5]])
        # the brow to the chin, forward of the ear: the line the hair and the collar do not cover
        rows = rows[(X[rows, 2] > ear_z + 0.03) & (X[rows, 1] < X[mp[168], 1] + 0.065) & (X[rows, 1] > X[lm['menton'], 1] - 0.005)]
        d, j = cKDTree(E).query(Pm[rows])
        rows, target = rows[d < 14], E[j[d < 14]]
        w = np.sqrt(120.0 / max(len(rows), 1))

        def res(q):
            c = np.concatenate([[turn], q])
            a = (project(P, c, centre)[0] - ob) / 6.0
            b = (project(X[rows], c, centre)[0] - target) * w / 2.0
            return np.concatenate([np.tanh(a.ravel() / 3) * 3, b.ravel(), [(c[3] / scale - 1) / 0.01 * 3]])
        cam = np.concatenate([[turn], least_squares(res, cam[1:], x_scale='jac').x])
    miss = np.linalg.norm(project(X[rows], cam, centre)[0] - target, axis=1).mean() / cam[3] * 1000
    return cam, float(miss)


def read_views(rec, sheet, head):
    """Each view of the record: its picture, the figure in it, its camera, and what of it is
    clothing or jewellery."""
    from scipy import ndimage
    X, tri, mp, lm = head['X'], head['tri'], head['mp'], head['lm']
    T = tri[X[tri][:, :, 1].mean(1) > X[:, 1].max() - HEAD_DROP_M]
    idx = sorted(mp)
    centre = X[[mp[i] for i in idx]].mean(0)
    xmid = float(X[[mp[i] for i in (168, 6, 4, 1) if i in mp], 0].mean())
    views = []
    for spec in rec['views']:
        x0, y0, x1, y1 = spec['crop_px']
        img = sheet[y0:y1, x0:x1].copy()
        size = (x1 - x0, y1 - y0)
        fg = figure_mask(img)
        pts = np.asarray(spec['points_px'], float) - np.array([x0, y0]) if spec.get('points_px') else None
        v = {'name': spec['name'], 'img': img, 'fg': fg, 'size': size, 'pts': pts}
        if spec['name'] == 'front':
            use = [i for i in idx if spec.get('camera') != 'upper_face' or X[mp[i], 1] > X[lm['subnasale'], 1] + 0.004]
            v['cam'] = solve_camera(X[[mp[i] for i in use]], pts[use], centre, (-0.3, 0.0, 0.3))
            v['miss_mm'] = float(np.sqrt(((project(X[[mp[i] for i in use]], v['cam'], centre)[0] - pts[use]) ** 2).sum(1).mean()) / v['cam'][3] * 1000)
        elif spec['name'] == 'back':
            v['cam'] = np.array([np.pi, 0.0, 0.0, np.mean([w['cam'][3] for w in views if w['name'] in ('left', 'right')]), 0.0, 0.0])
        else:
            # A side view is turned as the fit placed its own side view (the face was shaped to
            # match the picture from there); with no such fit, as the record reads it by eye.
            turn = np.copysign(head['side_turn_deg'] or abs(spec['turn_deg']), spec['turn_deg'])
            v['cam'], v['miss_mm'] = side_camera(head, T, pts, fg, turn, centre, size, views[0]['cam'][3])
        views.append(v)
    for v in views:
        img, fg, cam = v['img'], v['fg'], v['cam']
        W, H = v['size']
        lab, sizes = bright_parts(img, fg)
        big = [k + 1 for k in np.nonzero(sizes > 900)[0]]
        if v['name'] == 'back':
            # The collar's top at the nape, at the height the left view reads it, places the back view.
            tops = [np.nonzero(lab == k)[0].min() for k in big if np.nonzero(lab == k)[0].mean() > H * 0.45]
            row = min(tops) if tops else H * 0.6
            cols = np.nonzero(fg[int(row) - 6])[0]
            nape = np.array([[xmid, next(w['nape_y'] for w in views if w['name'] == 'left'), 0.0]])
            at = project(nape, cam, centre)[0][0]
            cam[4] += (cols.min() + cols.max()) / 2 - at[0]
            # ...across. Its height is the hair's top, which every level view sees at one height:
            # the other views' own reading of it (the collar's nape alone sat the head centimetres off).
            tops = [centre[1] + (w['cam'][5] - np.nonzero(w['fg'].any(1))[0].min()) / w['cam'][3] for w in views if w['name'] != 'back']
            cam[5] = np.nonzero(fg.any(1))[0].min() + cam[3] * (float(np.median(tops)) - centre[1])
            chin_row = row - 30
        else:
            chin_row = project(X[lm['menton']][None], cam, centre)[0][0, 1]
        cloth = np.zeros((H, W), bool)
        for k in big:
            ys, xs = np.nonzero(lab == k)
            if ys.mean() < chin_row + 4:        # a grey temple, not a collar
                continue
            top = np.full(W, H)
            np.minimum.at(top, xs, ys)
            for x in np.unique(xs):
                cloth[top[x]:, x] = True
        cols = np.nonzero(cloth.any(0))[0]
        if len(cols):
            # ...and beside the collar's ends, from each end's own height down (a coat's collar
            # stands behind a white one at the nape, and is dark like the hair above it).
            tops = np.array([np.nonzero(cloth[:, x])[0].min() for x in cols])
            cloth[int(np.median(tops[:6])):, :cols.min()] = True
            cloth[int(np.median(tops[-6:])):, cols.max() + 1:] = True
        cloth = ndimage.binary_dilation(cloth, iterations=9)
        if cloth.any():                          # below the collar's lowest top everything is clothing
            cloth[int(max(np.nonzero(cloth[:, x])[0].min() for x in np.nonzero(cloth.any(0))[0])):, :] = True
        if v['name'] in ('left', 'right') and (cloth & fg).any():
            # The nape: where the collar meets the back of the neck, as a height on the midline plane.
            ys, xs = np.nonzero(cloth & fg)
            behind = xs > np.median(xs) if v['name'] == 'left' else xs < np.median(xs)
            j = np.argmin(ys[behind])
            px, py = xs[behind][j], ys[behind][j]
            Rt = F.rot(*cam[:3]).T
            yx, yy = (px - cam[4]) / cam[3], -(py - cam[5]) / cam[3]
            yz = (xmid - centre[0] - Rt[0, 0] * yx - Rt[0, 1] * yy) / Rt[0, 2]
            v['nape_y'] = float(centre[1] + Rt[1, 0] * yx + Rt[1, 1] * yy + Rt[1, 2] * yz)
        jewel = np.zeros((H, W), bool)
        if rec.get('jewellery') == 'earrings':
            lobes = project(X[[lm['ear_lobe_r'], lm['ear_lobe_l']]], cam, centre)[0]
            for k in np.nonzero((sizes > 10) & (sizes <= 900))[0]:
                ys, xs = np.nonzero(lab == k + 1)
                c = np.array([xs.mean(), ys.mean()])
                if any(np.linalg.norm(c - p) < 34 and c[1] > p[1] - 12 for p in lobes):
                    jewel |= lab == k + 1
            jewel = ndimage.binary_dilation(jewel, iterations=4)
            if jewel.any():
                v['img'] = diffuse_fill(img, jewel)
        v['good'] = (ndimage.binary_erosion(fg, iterations=6) & ~cloth).astype(np.float32)   # in from the white ground's halo
        v['head'] = fg & ~cloth                  # the head and its hair, down to the collar
        v['left_out'] = {'clothing_px': int((cloth & fg).sum()), 'jewellery_px': int(jewel.sum())}
    return views, T, centre, xmid


def bones_rest(asset, names):
    """Bones' bind-pose places in the body's own space (the unoptimised GLB)."""
    import struct
    blob = (ROOT / 'assets/humans' / f'{asset}.lod0.glb').read_bytes()
    n = struct.unpack('<I', blob[12:16])[0]
    gltf, binary = json.loads(blob[20:20 + n]), blob[28 + n:]
    mi = next(i for i, m in enumerate(gltf['meshes']) if '_body_' in m['name'])
    skin = gltf['skins'][next(nd for nd in gltf['nodes'] if nd.get('mesh') == mi)['skin']]
    acc = gltf['accessors'][skin['inverseBindMatrices']]
    view = gltf['bufferViews'][acc['bufferView']]
    off = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    ibm = np.frombuffer(binary, dtype='<f4', count=acc['count'] * 16, offset=off).reshape(-1, 4, 4).transpose(0, 2, 1).astype(float)
    name = [gltf['nodes'][j].get('name') for j in skin['joints']]
    return {k: np.linalg.inv(ibm[name.index(k)])[:3, 3] for k in names}


def open_edges(tri):
    """The edges only one triangle uses: the surface's open boundary."""
    uses = {}
    for t in tri:
        for k in range(3):
            a, b = int(t[k]), int(t[(k + 1) % 3])
            uses[(min(a, b), max(a, b))] = uses.get((min(a, b), max(a, b)), 0) + 1
    return [e for e, c in uses.items() if c == 1]


def blink_shape(head):
    """How a blink moves the body's skin (metres, a row a vertex): renderers/web/js/human-skin.js
    shapeBlink, on the same rest body and with its own measures (BLINK there). The lids turn
    about each eye's centre, the upper edge down to `meet` of the way up from the lower, the
    lower up to the same line, the skin beyond each edge following less and less."""
    src = (ROOT / 'renderers/web/js/human-skin.js').read_text()
    B = {k: float(v) for k, v in re.findall(r'(\w+):\s*([0-9.]+)', re.search(r'export const BLINK = Object\.freeze\(\{([^}]*)\}\)', src).group(1))}
    P, tri = head['rest'], head['tri']
    bone = bones_rest(head['asset'], ('head', 'eye_l', 'eye_r'))
    o = (bone['eye_l'] + bone['eye_r']) / 2
    x = bone['eye_l'] - bone['eye_r']
    x /= np.linalg.norm(x)
    y = np.array([0.0, 1.0, 0.0]) - x * x[1]
    y /= np.linalg.norm(y)
    z = np.cross(x, y)
    if z @ (o - bone['head']) < 0:
        z = -z
    frame = np.stack([x, y, z])
    L = (P - o) @ frame.T * 100                      # the face's frame, cm
    # The lids' edges: the skin's open boundary round each eye.
    uses = open_edges(tri)
    near = lambda q: 0.8 < abs(q[0]) < 5.5 and abs(q[1]) < 1.6 and q[2] > -1.5
    out = np.zeros_like(P)
    for side, eye in ((1, 'eye_l'), (-1, 'eye_r')):
        edges = [(L[a], L[b]) for a, b in uses if near(L[a]) and near(L[b]) and np.sign(L[a][0]) == side == np.sign(L[b][0])]
        if len(edges) < 6:
            continue
        pts = [q for e in edges for q in e]
        ax = np.abs([q[0] for q in pts])
        x0, x1 = ax.min(), ax.max()
        inner, outer = pts[int(ax.argmin())], pts[int(ax.argmax())]
        chord = lambda v: inner[1] + (outer[1] - inner[1]) * (v - x0) / max(1e-6, x1 - x0)
        seen, U, D = [], [], []
        for la, lb in edges:
            m = (la + lb) / 2
            if any(np.linalg.norm(m - q) < 0.01 for q in seen):
                continue
            seen.append(m)
            (U if m[1] > chord(abs(m[0])) else D).extend([[abs(la[0]), la[1], la[2]], [abs(lb[0]), lb[1], lb[2]]])
        if len(U) < 4 or len(D) < 4:
            continue
        U, D = np.unique(np.round(U, 6), axis=0), np.unique(np.round(D, 6), axis=0)   # sorted across the eye
        at = lambda pts, v: np.array([np.interp(v, pts[:, 0], pts[:, 1]), np.interp(v, pts[:, 0], pts[:, 2])])
        x0, x1 = min(U[0, 0], D[0, 0]), max(U[-1, 0], D[-1, 0])
        c = (bone[eye] - o) @ frame.T * 100
        for i in np.where((np.sign(L[:, 0]) == side) & (np.abs(L[:, 0]) > x0 - B['corner_cm']) & (np.abs(L[:, 0]) < x1 + B['corner_cm'])
                          & (L[:, 2] > c[2] - 0.2) & (np.abs(L[:, 1] - c[1]) < 2.5))[0]:
            v, yy, zz = abs(L[i, 0]), L[i, 1], L[i, 2]
            u, l = at(U, v), at(D, v)
            meet = l[0] + B['meet'] * (u[0] - l[0])
            wc = 1 - smooth(0, B['corner_cm'], max(x0 - v, v - x1, 0))
            upper = yy >= (u[0] + l[0]) / 2
            edge, h = (u, yy - u[0]) if upper else (l, l[0] - yy)
            w = (1 - smooth(0, B['upper_cm'] if upper else B['lower_cm'], max(0, h))) * wc
            if w <= 0:
                continue
            r = np.hypot(edge[0] - c[1], edge[1] - c[2])
            th = (np.arctan2(meet - c[1], np.sqrt(max(0, r * r - (meet - c[1]) ** 2))) - np.arctan2(edge[0] - c[1], edge[1] - c[2])) * w
            dy, dz = yy - c[1], zz - c[2]
            out[i] = (y * (dz * np.sin(th) + dy * np.cos(th) - dy) + z * (dz * np.cos(th) - dy * np.sin(th) - dz)) / 100
    return out


def rest_lids(head, front, centre):
    """How far the lids rest shut (0..1 of a blink), so the eyes open as far as the front
    picture's. The picture's opening is between MediaPipe's lid middles, which lie on the lids'
    edges; the face's is between its own lids' edges there (the skin's open boundary: the
    mesh's vertices for those points sit a little back from the edge)."""
    mp, X = head['mp'], head['X']
    pairs = [(up, lo) for up, lo in LID_PAIRS if up in mp and lo in mp]
    if front['pts'] is None or not pairs:
        return None
    shut = blink_shape(head)
    rim = np.unique(np.array(open_edges(head['tri'])))
    edge = []
    for up, lo in pairs:
        mid = (X[mp[up]] + X[mp[lo]]) / 2
        at = rim[(np.abs(X[rim, 0] - mid[0]) < LID_EDGE_M[0]) & (np.abs(X[rim, 1] - mid[1]) < LID_EDGE_M[1]) & (X[rim, 2] > mid[2] - LID_EDGE_M[2])]
        if len(at) < 2:
            return None
        edge.append((int(at[np.argmax(X[at, 1])]), int(at[np.argmin(X[at, 1])])))
    k = 1000 / front['cam'][3]

    def opens(rest):
        P, _ = project(X + shut * rest, front['cam'], centre)
        return [float(np.linalg.norm(P[a] - P[b])) * k for a, b in edge]
    want = [float(np.linalg.norm(front['pts'][up] - front['pts'][lo])) * k for up, lo in pairs]
    lo, hi = 0.0, LID_REST_MOST
    if np.mean(opens(0)) <= np.mean(want):
        hi = 0.0
    else:
        for _ in range(24):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if np.mean(opens(mid)) > np.mean(want) else (lo, mid)
    rest = round(hi, 3)
    return {'picture_open_mm': [round(a, 1) for a in want], 'fitted_open_mm': [round(a, 1) for a in opens(0)],
            'rested_open_mm': [round(a, 1) for a in opens(rest)], 'rest': rest, 'shut': shut}


def read_eyes(front):
    """Each eye's iris and the white beside it, from the front picture. The lids hide part of
    every iris, so it is read as rings: the middle colour at each distance from the iris's
    centre, over what of it shows (the picture's points give the centre and the rim; what shows
    is told from the lids by its colour, far less of the skin's own beside the eye), and drawn
    whole from those; a catchlight is no ring's middle colour. Returns the two squares (the
    body's left eye first), the colour of the whites, and each iris's radius in the picture;
    None where the picture has no iris points or shows too little of an eye."""
    from scipy import ndimage
    pts, img = front['pts'], front['img']
    if pts is None or len(pts) < 478:
        return None
    S = EYES['size']
    squares, whites, radii = [], [], []
    for rim, mid, ring in EYE_RIMS:
        c = pts[mid]
        R = float(np.mean(np.linalg.norm(pts[list(ring)] - c, axis=1)))
        x0, y0 = int(c[0] - 3.2 * R), int(c[1] - 3.2 * R)
        win = img[max(y0, 0):int(c[1] + 3.2 * R), max(x0, 0):int(c[0] + 3.2 * R)]
        yy, xx = np.mgrid[0:win.shape[0], 0:win.shape[1]]
        xx, yy = xx + max(x0, 0), yy + max(y0, 0)
        hull = inside_hull(pts[list(rim)], np.stack([xx.ravel(), yy.ravel()], 1).astype(float)).reshape(win.shape[:2])
        rho = np.hypot(xx - c[0], yy - c[1]) / R
        lab = to_lab(win)
        chroma = np.hypot(lab[:, :, 1], lab[:, :, 2])
        # The skin's own colour: the cheek under the eye.
        cheek = (rho > 1.6) & (rho < 2.8) & (yy > c[1] + 0.9 * R) & ~ndimage.binary_dilation(hull, iterations=3)
        if cheek.sum() < 12:
            return None
        skin = float(np.median(chroma[cheek]))
        # ...below the upper lid's shadow and the catchlights, which lie over the iris's top.
        iris = (rho < 1.0) & (chroma < EYE_CHROMA[0] * skin) & (yy >= c[1] - EYE_ABOVE * R)
        step = 0.5 / R                               # half a pixel a ring
        edges = np.arange(0, 1.0 + step, step)
        rings = np.full((len(edges) - 1, 3), np.nan)
        for k in range(len(edges) - 1):
            px = win[iris & (rho >= edges[k] - step) & (rho < edges[k + 1] + step)]
            if len(px) >= 3:
                rings[k] = np.median(px, axis=0)
        ok = ~np.isnan(rings[:, 0])
        if ok.sum() < 6:
            return None
        at = (edges[:-1] + edges[1:]) / 2
        rings = np.stack([np.interp(at, at[ok], rings[ok, ch]) for ch in range(3)], 1)
        # The white: the lighter half of what shows beside the iris with less of the skin's colour.
        beside = hull & (rho > 1.15) & (rho < 2.2) & (chroma < EYE_CHROMA[1] * skin)
        if beside.sum() >= 4:
            px = win[beside]
            white = px[np.argsort(-lab[:, :, 0][beside])[:max(3, len(px) // 2)]].mean(0)
        else:
            white = rings[-1]
        # ...less of its colour: the few pixels beside an iris are part lid and part lash.
        white = white.mean() + (white - white.mean()) * EYE_WHITE_COLOUR
        # The square: the iris's rings out to its rim, the white beyond it.
        v, u = (np.mgrid[0:S, 0:S] + 0.5) / S - 0.5
        r = np.hypot(u, v) / EYE_DISC
        sq = np.stack([np.interp(r, at, rings[:, ch]) for ch in range(3)], -1)
        w = smooth(0.94, 1.1, r)[:, :, None]
        squares.append(sq * (1 - w) + white * w)
        whites.append(white)
        radii.append(R)
    return {'squares': squares, 'white': np.mean(whites, 0), 'iris_px': radii}


def weld(rest):
    """The kit's vertices that are one point of the body (its UV layout splits them): a group each."""
    _, group = np.unique(np.round(rest / 1e-6).astype(np.int64), axis=0, return_inverse=True)
    return group.ravel()


def inside_hull(pts, q):
    """Which of the 2-D points q lie inside the convex hull of pts."""
    from scipy.spatial import ConvexHull
    h = ConvexHull(pts)
    return (q @ h.equations[:, :2].T + h.equations[:, 2] <= 1e-9).all(1)


def to_lab(rgb):
    """sRGB (0..1) as CIE L*a*b*."""
    c = srgb_to_linear(rgb) @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T
    f = c / np.array([0.9505, 1.0, 1.089])
    f = np.where(f > 0.008856, np.cbrt(f), 7.787 * f + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def hair_shown(views, head, T, centre):
    """Where the pictures show hair on the fitted head and where they show skin: 1 to 0 for each
    kit vertex of the head. The skin's colour is the front view's own, inside the face above the
    nose's base; the hair's colours are what stands outside the fitted head's outline above the
    ear lobes; a vertex is read in every view that sees it, by which of the two its colour is
    nearer, and one no view sees takes its neighbours' reading. What clothing covers is not hair."""
    from scipy import ndimage
    from scipy.cluster.vq import kmeans2
    X, mp, lm = head['X'], head['mp'], head['lm']
    group = weld(head['rest'])
    N = np.zeros_like(X)
    np.add.at(N, group, vertex_normals(X, head['tri']))
    N = (N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12))[group]
    hv = np.unique(T)
    idx = sorted(mp)
    seen, skin_px, hair_px = [], [], []
    for v in views:
        W, H = v['size']
        P, z = project(X, v['cam'], centre)
        zb, tb, _ = raster(P, z, T, v['size'])
        soft = np.stack([ndimage.gaussian_filter(v['img'][:, :, c], 1.5) for c in range(3)], -1)
        xi, yi = np.clip(P[hv, 0].astype(int), 0, W - 1), np.clip(P[hv, 1].astype(int), 0, H - 1)
        nz = (N[hv] @ F.rot(*v['cam'][:3]).T)[:, 2]
        vis = (z[hv] > ndimage.maximum_filter(zb, 3)[yi, xi] - 0.004) & (nz > 0.15) & v['fg'][yi, xi]
        seen.append((vis, nz, to_lab(soft[yi, xi]), v['good'][yi, xi] > 0.5))
        lobe = project(X[[lm['ear_lobe_l'], lm['ear_lobe_r']]], v['cam'], centre)[0][:, 1].min()
        out = v['head'] & ~ndimage.binary_dilation(tb >= 0, iterations=4)
        out[int(lobe):] = False
        hair_px.append(to_lab(soft[out]))
        if v['name'] == 'front':
            Pf = P[hv]
            face = inside_hull(P[[mp[i] for i in idx]], Pf) & vis & (X[hv, 1] > X[lm['subnasale'], 1] + 0.004)
            skin_px.append(to_lab(soft[yi[face], xi[face]]))
    skin_px, hair_px = np.concatenate(skin_px), np.concatenate(hair_px)
    mu = np.median(skin_px, 0)
    sd = np.maximum(1.4826 * np.median(np.abs(skin_px - mu), 0), HAIR_SKIN_SPREAD)
    hair_px = hair_px[(((hair_px - mu) / sd) ** 2).sum(1) > 9]
    if len(hair_px) < 200:
        return np.zeros(len(X)), {'skin_lab': [round(float(c), 1) for c in mu], 'hair_px': int(len(hair_px))}
    cen, _ = kmeans2(hair_px[::max(1, len(hair_px) // 20000)], HAIR_COLOURS, minit='++', seed=7)
    num, den = np.zeros(len(hv)), np.zeros(len(hv))
    for vis, nz, col, bare in seen:
        ds = (((col - mu) / sd) ** 2).sum(1)
        dh = (((col[:, None, :] - cen[None]) / sd) ** 2).sum(2).min(1)
        w = vis * np.clip(nz, 0, 1) ** 2
        num += w * np.where(bare, ds / np.maximum(ds + dh, 1e-9), 0.0)
        den += w
    # One point of the body is one reading, and what no view sees takes its neighbours'.
    _, gi = np.unique(group[hv], return_inverse=True)
    G = gi.max() + 1
    gn, gd = np.bincount(gi, num, G), np.bincount(gi, den, G)
    loc = np.full(len(X), -1)
    loc[hv] = gi
    e = np.concatenate([loc[T[:, [0, 1]]], loc[T[:, [1, 2]]], loc[T[:, [2, 0]]]])
    e = np.unique(np.sort(e[e[:, 0] != e[:, 1]], 1), axis=0)
    from scipy import sparse
    A = sparse.coo_matrix((np.ones(2 * len(e)), (np.concatenate([e[:, 0], e[:, 1]]), np.concatenate([e[:, 1], e[:, 0]]))), shape=(G, G)).tocsr()
    known = gd > 0.02
    h = np.where(known, gn / np.maximum(gd, 1e-9), 0.0)
    wgt = known.astype(float)
    for _ in range(40):
        if wgt.min() > 0:
            break
        h2, w2 = A @ (h * wgt), A @ wgt
        fill = (wgt == 0) & (w2 > 0)
        h[fill] = h2[fill] / w2[fill]
        wgt[fill] = 1.0
    deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
    for _ in range(2):
        h = 0.5 * h + 0.5 * (A @ h) / deg
    out = np.zeros(len(X))
    out[hv] = h[gi]
    return out, {'skin_lab': [round(float(c), 1) for c in mu], 'hair_px': int(len(hair_px))}


def grow(rec, views, head, T, centre):
    """How far the stand-in's hair (and a beard) stands out from the fitted skin: a distance for
    each kit vertex of the head, metres, along the line from the middle of the head out through
    that vertex, and that middle. The pictures give it. Pushed out along its line, a vertex
    leaves the fitted head's own outline in a view after one distance and the picture's outline
    after another; the difference, foreshortened by how far the line leans toward that camera,
    is the hair's depth there (exactly so on a round head, and on any head where the line runs
    across the view, at the outline itself). Each view's reading counts by how squarely it sees
    the line from the side; the answer never passes the hull the four outlines allow (a point of
    the hair is inside the figure in every view), is smoothed a little, and nothing is grown on
    the face, the lips or the ears. Measuring from the head's own outline is what keeps an ear
    from being read as hair in front of it. With no `grow` in the record nothing is grown."""
    from scipy import sparse
    X, mp, lm = head['X'], head['mp'], head['lm']
    spec = rec.get('grow')
    mid = (X[lm['ear_top_l']] + X[lm['ear_top_r']]) / 2
    out = np.zeros(len(X))
    if not spec:
        return out, mid
    hv = np.unique(T)
    group = weld(head['rest'])
    _, gi = np.unique(group[hv], return_inverse=True)
    G = gi.max() + 1
    Xg = np.zeros((G, 3))
    np.add.at(Xg, gi, X[hv])
    Xg /= np.bincount(gi, minlength=G)[:, None]
    U = Xg - mid
    U /= np.maximum(np.linalg.norm(U, axis=1, keepdims=True), 1e-9)
    most = spec['max_cm'] / 100
    steps = np.arange(0, GROW_FEEL_M + GROW_STEP_M / 2, GROW_STEP_M)
    hull = np.full(G, most)
    num, den = np.zeros(G), np.zeros(G)
    for v in views:
        W, H = v['size']
        P, z = project(X, v['cam'], centre)
        own = raster(P, z, T, v['size'])[1] >= 0
        P0 = project(Xg, v['cam'], centre)[0]
        dP = project(Xg + U, v['cam'], centre)[0] - P0
        px = P0[:, None, :] + steps[None, :, None] * dP[:, None, :]
        xi, yi = np.floor(px[:, :, 0]).astype(int), np.floor(px[:, :, 1]).astype(int)
        within = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
        xi, yi = np.clip(xi, 0, W - 1), np.clip(yi, 0, H - 1)

        def reach(mask):
            # the last step still inside; a vertex that starts outside is not pushed at all
            inside = within & mask[yi, xi]
            first = np.where(inside.all(1), len(steps), np.argmin(inside, 1))
            return steps[np.maximum(first - 1, 0)]
        far, near = reach(v['head']), reach(own)
        across = np.sqrt(np.clip(1 - (U @ F.rot(*v['cam'][:3])[2]) ** 2, 0, 1))
        w = across ** spec.get('view_power', 6) * (far < steps[-1])
        num += w * np.clip(far - near, 0, None) * across
        den += w
        hull = np.minimum(hull, far)
    t = np.minimum(num / np.maximum(den, 1e-9), hull)
    # Only where the pictures show hair: skin does not stand out from itself.
    hair = np.zeros(G)
    np.maximum.at(hair, gi, head['hair'][hv])
    t = t * smooth(HAIR_GROWS[0], HAIR_GROWS[1], hair)
    # Nothing grows on the face (inside the points MediaPipe reads on it), the lips, or the ears.
    front = next(v for v in views if v['name'] == 'front')
    Pf = project(Xg, front['cam'], centre)[0]
    idx = sorted(mp)
    face = inside_hull(project(X[[mp[i] for i in idx]], front['cam'], centre)[0], Pf) & (U[:, 2] > 0.15)
    if spec.get('beard'):
        # ...but a beard does, below the nose's base, off the lips.
        lips = inside_hull(project(X[[mp[i] for i in LIPS if i in mp]], front['cam'], centre)[0], Pf)
        face &= (Xg[:, 1] > X[lm['subnasale'], 1] - 0.002) | lips
    still = face.copy()
    for side_ in 'lr':
        ear = (X[lm[f'ear_top_{side_}']] + X[lm[f'ear_lobe_{side_}']]) / 2
        still |= np.linalg.norm(Xg - ear, axis=1) < spec.get('ear_cm', 2.6) / 100
    t[still] = 0
    # ...and it is smoothed over the mesh, still inside the hull.
    loc = np.full(len(X), -1)
    loc[hv] = gi
    e = np.concatenate([loc[T[:, [0, 1]]], loc[T[:, [1, 2]]], loc[T[:, [2, 0]]]])
    e = np.unique(np.sort(e[e[:, 0] != e[:, 1]], 1), axis=0)
    A = sparse.coo_matrix((np.ones(2 * len(e)), (np.concatenate([e[:, 0], e[:, 1]]), np.concatenate([e[:, 1], e[:, 0]]))), shape=(G, G)).tocsr()
    deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
    for _ in range(spec.get('smooth', 3)):
        t = np.clip(0.5 * t + 0.5 * (A @ t) / deg, 0, hull)
        t[still] = 0
    out[hv] = t[gi]
    return out, mid


def bake(rec, sheet, head):
    from scipy import ndimage
    from scipy.interpolate import RBFInterpolator
    views, T, centre, xmid = read_views(rec, sheet, head)
    # The lids first: the fitted face's eyes stand wider open than the pictures', so its lids
    # are rested as far shut as the front picture shows them, and everything after (the
    # cameras again, the pictures laid on the skin) is of that face.
    lids = rest_lids(head, views[0], centre)
    if lids and lids['rest'] > 0:
        head['X'] = head['X'] + lids.pop('shut') * lids['rest']
        views, T, centre, xmid = read_views(rec, sheet, head)
    elif lids:
        lids.pop('shut')
    X0, uv, mp, lm = head['X'], head['uv'], head['mp'], head['lm']
    eyes = read_eyes(views[0])
    # The hair's own shape: the skin pushed out to the pictures' outlines, and the pictures
    # laid on that (the cameras were found on the bare, fitted head).
    head['hair'], read = hair_shown(views, head, T, centre)
    thick, mid = grow(rec, views, head, T, centre)
    out = X0 - mid
    X = X0 + out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-9) * thick[:, None]
    group = weld(head['rest'])
    N = np.zeros_like(X)
    np.add.at(N, group, vertex_normals(X, head['tri']))
    N = (N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12))[group]
    idx = sorted(mp)
    hv = np.unique(T)
    for v in views:
        P, z = project(X, v['cam'], centre)
        zb, _, _ = raster(P, z, T, v['size'])
        Pw = P.copy()
        if v['name'] == 'front':
            # The picture's own features onto the mesh's: a thin-plate spline through the points.
            src, dst = P[[mp[i] for i in idx]], v['pts'][idx]
            Pw[hv] = P[hv] + RBFInterpolator(src, dst - src, kernel='thin_plate_spline', smoothing=2.0)(P[hv])
        v.update(P=P, Pw=Pw, z=z, zb=ndimage.maximum_filter(zb, 3), nz=(N @ F.rot(*v['cam'][:3]).T)[:, 2])
    TW, TH = TEXTURE_PX
    tex = np.zeros((TH, TW, 3), np.float32)
    alpha = np.zeros((TH, TW), np.float32)
    seen = np.zeros((TH, TW), np.float32)
    cover = np.zeros((TH, TW), bool)
    front = np.zeros((TH, TW), np.float32)
    lateral = np.zeros((TH, TW), np.float32)
    height = np.zeros((TH, TW), np.float32)
    stand = np.zeros((TH, TW), np.float32)
    hairy = np.zeros((TH, TW), np.float32)
    facing = np.zeros((TH, TW, 3), np.float32)
    chin = X[lm['menton'], 1]
    for r in RECTS:
        (u0, v0, u1, v1), (x0, y0, x1, y1) = r['uv'], r['px']
        tuv = uv[T]
        inside = ((tuv[:, :, 0] >= u0) & (tuv[:, :, 0] <= u1) & (tuv[:, :, 1] >= v0) & (tuv[:, :, 1] <= v1)).all(1)
        Tr = T[inside]
        W_, H_ = x1 - x0, y1 - y0
        Puv = np.stack([(uv[:, 0] - u0) / (u1 - u0) * W_, (uv[:, 1] - v0) / (v1 - v0) * H_], 1)
        _, tb, bary = raster(Puv, np.zeros(len(uv)), Tr, (W_, H_))
        m = tb >= 0
        t, b = Tr[tb[m]], bary[m].astype(np.float64)
        pos = (X[t] * b[:, :, None]).sum(1)
        lat = np.abs(pos[:, 0] - xmid)
        th = (thick[t] * b).sum(1)
        raw, cols = [], []
        for v in views:
            W, H = v['size']
            p = (v['P'][t] * b[:, :, None]).sum(1)
            pw = (v['Pw'][t] * b[:, :, None]).sum(1)
            zz, nz = (v['z'][t] * b).sum(1), (v['nz'][t] * b).sum(1)
            xi, yi = np.clip(p[:, 0].astype(int), 0, W - 1), np.clip(p[:, 1].astype(int), 0, H - 1)
            w = (zz > v['zb'][yi, xi] - 0.012) * ((pw[:, 0] > 1) & (pw[:, 0] < W - 1) & (pw[:, 1] > 1) & (pw[:, 1] < H - 1))
            w = w * smooth(0.6, 1.0, sample(v['good'][:, :, None], pw)[:, 0])
            if v['name'] == 'front':
                # ...the face's own width of it, and past that only hair that stands out and faces it
                w = w * smooth(0.12, 0.45, nz) * (1 - smooth(0.050, 0.066, lat) * (1 - smooth(0.003, 0.010, th)))
            elif v['name'] == 'back':
                w = w * smooth(0.10, 0.5, nz)
            else:
                w = w * smooth(0.08, 0.4, nz) * smooth(-0.005, 0.02, (1.0 if v['name'] == 'left' else -1.0) * (pos[:, 0] - xmid))
            raw.append(w)
            cols.append(sample(v['img'], pw))
        # The front first; what it leaves goes to whichever other view sees the texel best.
        wf = raw[0]
        others = np.stack(raw[1:], 1)
        share = others ** 2
        share = share / np.maximum(share.sum(1, keepdims=True), 1e-9) * np.clip(others.max(1, keepdims=True) * 3, 0, 1)
        ws = np.concatenate([wf[:, None], (1 - wf)[:, None] * share], 1)
        tot = ws.sum(1)
        tex[y0:y1, x0:x1][m] = sum(cols[k] * ws[:, k:k + 1] for k in range(len(views))) / np.maximum(tot, 1e-6)[:, None]
        seen[y0:y1, x0:x1][m] = np.clip(tot, 0, 1)
        cover[y0:y1, x0:x1][m] = True
        front[y0:y1, x0:x1][m] = wf
        lateral[y0:y1, x0:x1][m] = lat
        height[y0:y1, x0:x1][m] = pos[:, 1]
        stand[y0:y1, x0:x1][m] = th
        hairy[y0:y1, x0:x1][m] = (head['hair'][t] * b).sum(1)
        facing[y0:y1, x0:x1][m] = (N[t] * b[:, :, None]).sum(1)
        # The head above the chin is whole; of the neck, only what a picture shows.
        whole = smooth(chin + NECK_KEEP_M[0], chin + NECK_KEEP_M[1], pos[:, 1]) if r['name'] != 'neck' else 0.0
        alpha[y0:y1, x0:x1][m] = np.maximum(np.clip(tot, 0, 1), whole)
    hole = cover & (seen < 0.35) & (alpha > 0.5)
    tex = diffuse_fill(tex, hole | ~cover, known=cover & ~hole)
    # The mask draws in from where the pictures stop, feathered, and bleeds past each island's edge.
    alpha = np.where(cover, ndimage.minimum_filter(np.where(cover, alpha, 1.0), 9), 0)
    soft = ndimage.gaussian_filter(np.where(cover, alpha, 0), 4.0) / np.maximum(ndimage.gaussian_filter(cover.astype(np.float32), 4.0), 1e-3)
    near = ndimage.distance_transform_edt(~cover, return_distances=False, return_indices=True)
    soft = soft[near[0], near[1]]
    stand = stand[near[0], near[1]]
    hairy = hairy[near[0], near[1]]
    facing = facing[near[0], near[1]]
    facing /= np.maximum(np.linalg.norm(facing, axis=2, keepdims=True), 1e-9)
    # The skin's own tone: the cheeks, as the front view shows them (linear light).
    cheek = cover & (front > 0.9) & (lateral > 0.02) & (lateral < 0.05)
    cheek &= (height < X[mp[168], 1] - 0.025) & (height > X[lm['stomion'], 1])
    if not cheek.any():
        sys.exit(f"{rec['person_id']}: the front view shows no cheek to take the skin's tone from")
    tone = srgb_to_linear(tex[cheek]).mean(0)
    # ...and the body's own map on the same skin (the head's rect), for the rest of the body's tint.
    (u0, v0, u1, v1), (x0, y0, x1, y1) = RECTS[0]['uv'], RECTS[0]['px']
    ys, xs = np.nonzero(cheek)
    base = base_map(head['asset'])
    bh, bw = base.shape[:2]
    bu = u0 + (xs + 0.5 - x0) / (x1 - x0) * (u1 - u0)
    bv = v0 + (ys + 0.5 - y0) / (y1 - y0) * (v1 - v0)
    own = srgb_to_linear(base[np.clip((bv * bh).astype(int), 0, bh - 1), np.clip((bu * bw).astype(int), 0, bw - 1)]).mean(0)
    tone = np.stack([tone, own])
    head['grown'] = X
    cams = {v['name']: {'yaw_deg': round(float(np.degrees(v['cam'][0])), 1), 'pitch_deg': round(float(np.degrees(v['cam'][1])), 1),
                        'roll_deg': round(float(np.degrees(v['cam'][2])), 1), 'px_per_m': round(float(v['cam'][3]), 1),
                        **({'miss_mm': round(v['miss_mm'], 2)} if 'miss_mm' in v else {}), **v['left_out']} for v in views}
    return tex, soft, tone, cams, {'stand': stand, 'hair': hairy, 'facing': facing, 'mid': mid, 'max_m': float(thick.max()), 'read': read, 'lids': lids, 'eyes': eyes}


def srgb_to_linear(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def compose(tex, soft, grown):
    """The sheet the renderer reads: the pictures, and in the spare column two quarter-scale
    blocks. The mask: where the sheet covers (green), how far the hair stands out from the skin
    as a share of the record's `reach_m` (red), and where the pictures show hair and not skin
    (blue). Under it, which way the grown surface faces (the body's rest frame, x y z as red
    green blue, -1..1 as 0..1). All are sRGB-coded, so a reader that decodes the sheet's colours
    gets their own values."""
    from PIL import Image
    TW, TH = TEXTURE_PX
    out = np.clip(tex, 0, 1).copy()
    mw, mh = int(TW * MASK['scale']), int(TH * MASK['scale'])
    shrink = lambda a: np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((mw, mh), Image.BOX)).astype(np.float32) / 255
    reach = grown['max_m']
    mask = np.stack([shrink(grown['stand'] / reach if reach > 0 else grown['stand'] * 0), shrink(soft), shrink(grown['hair'])], -1)
    facing = np.stack([shrink(grown['facing'][:, :, c] * 0.5 + 0.5) for c in range(3)], -1)
    for (mx, my), block in ((MASK['px'], mask), (SHAPE_PX, facing)):
        # a border of the block's own edge values, so a filtered read at its rim stays the block's
        out[my - 6:my + mh + 6, mx - 6:mx + mw + 6] = linear_to_srgb(np.pad(block, ((6, 6), (6, 6), (0, 0)), mode='edge'))
    if grown.get('eyes'):
        # ...and under those each eye's own iris (the body's left eye, then its right), with a
        # border of the whites' colour.
        (ex, ey), S = EYES['px'], EYES['size']
        out[ey - 6:ey + S + 6, ex - 6:ex + 2 * S + 6] = grown['eyes']['white']
        out[ey:ey + S, ex:ex + 2 * S] = np.concatenate(grown['eyes']['squares'], 1)
    return Image.fromarray((out * 255 + 0.5).astype(np.uint8))


def preview(head, tex, soft, path, turns=(0, -35, 35, -80, 80, 180), size=520):
    """A strip of turns of the bare head under the baked skin, to look at (not the renderer)."""
    from PIL import Image
    X, tri, uv = head.get('grown', head['X']), head['tri'], head['uv']
    N = vertex_normals(X, tri)
    top = head['X'][:, 1].max()
    T = tri[X[tri][:, :, 1].mean(1) > top - HEAD_DROP_M]
    centre = np.array([0, top - 0.115, 0.03])
    tiles = []
    for turn in turns:
        cam = np.array([np.radians(turn), np.radians(-3), 0, size / 0.42, size / 2, size / 2])
        P, z = project(X, cam, centre)
        _, tb, bary = raster(P, z, T, (size, size))
        m = tb >= 0
        t, b = T[tb[m]], bary[m].astype(np.float64)
        uvp = (uv[t] * b[:, :, None]).sum(1)
        n = ((N @ F.rot(*cam[:3]).T)[t] * b[:, :, None]).sum(1)
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        tp, ok = np.zeros_like(uvp), np.zeros(len(uvp), bool)
        for r in RECTS:
            (u0, v0, u1, v1), (x0, y0, x1, y1) = r['uv'], r['px']
            k = (uvp[:, 0] >= u0) & (uvp[:, 0] <= u1) & (uvp[:, 1] >= v0) & (uvp[:, 1] <= v1)
            tp[k, 0] = x0 + (uvp[k, 0] - u0) / (u1 - u0) * (x1 - x0)
            tp[k, 1] = y0 + (uvp[k, 1] - v0) / (v1 - v0) * (y1 - y0)
            ok |= k
        a = sample(soft[:, :, None], tp)[:, 0] * ok
        col = sample(tex, tp) * a[:, None] + np.array([0.80, 0.62, 0.52]) * (1 - a[:, None])
        light = np.array([0.25, 0.35, 0.9]) / np.linalg.norm([0.25, 0.35, 0.9])
        img = np.full((size, size, 3), 0.54, np.float32)
        img[m] = col * (0.55 + 0.45 * np.clip(n @ light, 0, 1))[:, None]
        tiles.append((np.clip(img, 0, 1) * 255).astype(np.uint8))
    Image.fromarray(np.concatenate(tiles, 1)).save(path, quality=90)


def detect(rec, sheet_path, model):
    """MediaPipe Face Landmarker's 478 points on each view that shows the face (sheet pixels),
    read on the view's quadrant at twice its size."""
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision
    from PIL import Image
    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path=str(model)), num_faces=1))
    sheet = Image.open(sheet_path).convert('RGB')
    for spec in rec['views']:
        if spec['name'] == 'back':
            continue
        x0, y0, x1, y1 = spec['crop_px']
        big = sheet.crop((x0, y0, x1, y1)).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.LANCZOS)
        r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(np.asarray(big))))
        if not r.face_landmarks:
            sys.exit(f"{rec['person_id']}: no face found in the {spec['name']} view")
        spec['points_px'] = [[round(x0 + l.x * (x1 - x0), 1), round(y0 + l.y * (y1 - y0), 1)] for l in r.face_landmarks[0]]
    det.close()


def texture_block(person, image_path, tone, grown):
    return {
        'file': str(image_path.relative_to(ROOT)),
        'size_px': list(TEXTURE_PX),
        'sha256': sha256(image_path),
        'bytes': image_path.stat().st_size,
        'rects': [{'name': r['name'], 'uv': list(r['uv']), 'px': list(r['px'])} for r in RECTS],
        'mask': {'px': list(MASK['px']), 'scale': MASK['scale']},
        'tone_linear': [round(float(x), 4) for x in tone[0]],
        'base_tone_linear': [round(float(x), 4) for x in tone[1]],
        'tint': [round(float(a / max(b, 1e-4)), 4) for a, b in zip(tone[0], tone[1])],
        # The hair's standing out from the skin (the mask's red): its greatest, metres, the
        # middle of the head it is measured out from (the body's rest frame, metres), where on
        # the sheet the grown surface's facing is kept, and what the pictures' colours read as.
        'grow': {'reach_m': round(grown['max_m'], 4), 'from_m': [round(float(x), 4) for x in grown['mid']],
                 'normal_px': list(SHAPE_PX), 'read': grown['read']},
        # How far the lids rest shut, so the eyes open as the front picture's do (0: as fitted).
        **({'lids': grown['lids']} if grown['lids'] else {}),
        # Each eye's own iris from the front picture (two squares side by side, the body's left
        # eye first), and the colour of the whites (sRGB).
        **({'eyes': {'px': list(EYES['px']), 'size': EYES['size'], 'white_srgb': [round(float(c), 3) for c in grown['eyes']['white']],
                     'iris_px': [round(r, 1) for r in grown['eyes']['iris_px']]}} if grown.get('eyes') else {}),
    }


def run(person, sheet_path, model=None, preview_path=None):
    from PIL import Image
    path = SKINS / f'{person}.json'
    rec = json.loads(path.read_text())
    if rec['sheet'].get('sha256') and sha256(sheet_path) != rec['sheet']['sha256']:
        sys.exit(f"{person}: {sheet_path} is not the sheet the record names (SHA-256 differs)")
    if model:
        detect(rec, sheet_path, model)
    sheet = np.asarray(Image.open(sheet_path).convert('RGB')).astype(np.float32) / 255
    head = fitted_head(person)
    tex, soft, tone, cams, grown = bake(rec, sheet, head)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f'{person}_skin.jpg'
    compose(tex, soft, grown).save(out, quality=JPEG_QUALITY, subsampling=0, optimize=True)
    rec['sheet']['sha256'] = sha256(sheet_path)
    rec['cameras'] = cams
    rec['fit_values_sha256'] = values_sha(person)
    rec['texture'] = texture_block(person, out, tone, grown)
    path.write_text(json.dumps(rec, indent=1) + '\n')
    if preview_path:
        preview(head, tex, soft, preview_path)
    print(f"{person}: {out.relative_to(ROOT)} {out.stat().st_size} bytes; cameras {json.dumps(cams)}")


def check():
    bad = []
    for path in sorted(SKINS.glob('*.json')):
        rec = json.loads(path.read_text())
        person = rec['person_id']
        if rec.get('format') != FORMAT:
            bad.append(f'{path.name}: format is not {FORMAT}')
            continue
        t = rec.get('texture')
        if not t:
            bad.append(f'{person}: no texture baked')
            continue
        f = ROOT / t['file']
        if not f.exists():
            bad.append(f"{person}: {t['file']} is missing")
        elif sha256(f) != t['sha256']:
            bad.append(f"{person}: {t['file']} is not the file the record baked (SHA-256 differs)")
        layout = {'size_px': list(TEXTURE_PX), 'rects': [{'name': r['name'], 'uv': list(r['uv']), 'px': list(r['px'])} for r in RECTS],
                  'mask': {'px': list(MASK['px']), 'scale': MASK['scale']}}
        if any(t.get(k) != v for k, v in layout.items()):
            bad.append(f'{person}: the texture layout in the record is not this tool\'s; bake again')
        g = t.get('grow') or {}
        if g.get('normal_px') != list(SHAPE_PX) or not (0 <= g.get('reach_m', -1) < 0.2) or len(g.get('from_m') or []) != 3:
            bad.append(f'{person}: the hair\'s standing out is not recorded as this tool records it; bake again')
        lids = t.get('lids')
        if lids is not None and not (0 <= lids.get('rest', -1) <= LID_REST_MOST):
            bad.append(f'{person}: the lids\' rest is not one this tool gives; bake again')
        e = t.get('eyes')
        if e is not None and (e.get('px') != list(EYES['px']) or e.get('size') != EYES['size']
                              or not (isinstance(e.get('white_srgb'), list) and len(e['white_srgb']) == 3 and all(0 < x < 1 for x in e['white_srgb']))):
            bad.append(f'{person}: the eyes are not recorded as this tool records them; bake again')
        if not rec.get('liberty') or f"### {rec['liberty']} " not in (ROOT / 'docs/LIBERTIES.md').read_text():
            bad.append(f"{person}: the record names no liberty that docs/LIBERTIES.md holds")
        if not (isinstance(t.get('tint'), list) and len(t['tint']) == 3 and all(0.2 < x < 5 for x in t['tint'])):
            bad.append(f'{person}: no tint for the rest of the body; bake again')
        if rec.get('fit_values_sha256') != values_sha(person):
            bad.append(f'{person}: the face was refitted since this skin was baked; bake again')
        src = ROOT / 'data/sources' / f"{rec['source']}.json"
        if not src.exists():
            bad.append(f"{person}: source {rec['source']} does not resolve")
        elif json.loads(src.read_text()).get('rights_status') != 'cleared':
            bad.append(f"{person}: source {rec['source']} is not rights-cleared; no asset may be derived from it")
        elif json.loads(src.read_text()).get('asset_use') != 'texture':
            bad.append(f"{person}: source {rec['source']} does not say its pixels are used as a texture (asset_use)")
    for b in bad:
        print('FAIL', b)
    if bad:
        sys.exit(1)
    print(f'likeness skins: {len(list(SKINS.glob("*.json")))} records hold')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('person', nargs='?')
    ap.add_argument('--sheet')
    ap.add_argument('--detect', metavar='MODEL')
    ap.add_argument('--preview', metavar='OUT')
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    if args.check:
        return check()
    if not args.person or not args.sheet:
        ap.error('PERSON and --sheet, or --check')
    run(args.person, args.sheet, args.detect, args.preview)


if __name__ == '__main__':
    main()
