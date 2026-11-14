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
    face's line against the sheet's white ground (down to the chin, or to the nose's base for a
    face with a beard, whose outline is not the jaw's), the back from the hair's top and the
    collar. Then the four are lined up with each other (`line_up`): every view shows the hair's
    outline, and the cameras are moved together until the solid the four outlines allow
    shadows as much of each outline as it can, each camera held by what it was solved on (a
    front view's points hardly say how far the head tilts toward the camera; the outlines do);
  - the lids come first (`rest_lids`): the fitted face's eyes stand wider open than the
    pictures', so the blink's own shape (renderers/web/js/human-skin.js shapeBlink, read here by
    `blink_shape`) is taken as far as closes them to the front picture's opening, between the
    lids' edges; the cameras are found again on that face, and `texture.lids.rest` tells the
    renderer to rest the lids the same;
  - the front view is then warped a little (a thin-plate spline through the points), so the
    picture's own lips, lids, nostrils and brows land on the mesh's;
  - the head is made finer first (`refine`: the scalp's triangles are 13 to 35 mm wide, too
    coarse to carry a knot's or a curl's outline), and then the hair (`hair_shown`, `grow`):
    each skin vertex is read as hair or skin by the pictures' colour at it (the face's own skin
    tone against the tones outside the bare head's outline), and the skin is moved out, along
    the line from the head's upright middle (`away`), by the hair's depth there: how far that
    line runs inside the solid the pictures' four outlines allow, less how far it runs inside
    the solid the bare head's own four outlines allow. It grows where the pictures show hair
    (by its colour, or by the outlines standing well outside the bare head: grey hair is the
    skin's colour), on a beard's ground for a record that has one where the lower face reads
    as hair, never on the face or the ears. Four outlines cannot say where a width is: hair
    that hangs behind the ears widens the front and back pictures beside the jaw and the
    temples, and the solid lays it on the cheeks and temples too. A record with
    `grow.cheek_cm` measures the face in front of the ears in a narrower solid and grows hair
    there only where its colour shows it. Then the grown head is fitted to the pictures
    (`fit_outlines`): drawn as each camera sees it, the points on its outline are moved along
    their lines to the picture's outline, and hair that stands in front of skin a picture
    shows (an ear, the neck under it) is drawn back. The pictures are laid on that grown head,
    and the record keeps where the hair stands out as cells of the sheet
    (`texture.grow.fine`), where the renderer splits the body's skin as finely
    (renderers/web/js/human-fine.js);
  - every texel of the head, eye sockets and neck in the body's own UV layout takes the view that sees
    it best. Within the face's own width the front goes first and the others share what it
    leaves. Past it, hair that stands out goes to whichever view sees it most squarely (the
    front counting for a fifth from the ears' lobes up, where it looks along the hair), skin
    (an ear) to its own side's picture, and hair at a temple to the side pictures. What no
    view sees squarely (the underside of a beard, which the front picture looks along) takes
    the picture that sees it at all (`GRAZE`). What no view sees (the crown, behind an ear) is
    filled from around it: hair with the hair beside it, mirrored in the hole's edge so it
    keeps its curl (`mirror_fill`), then the rest with its neighbours' colour, the texels the
    mask leaves out too (the mask is feathered, and left black they darkened its edge). Hair
    that stands out is covered wherever it stands (`HAIR_WHOLE_M`). Clothing (the collar and
    all below it) is left out, and earrings are painted over from the skin beside them;
  - one colour for each texel cannot be right from two sides. Hair beside the face is seen
    from the front as locks hanging down and from the side as the hair swept back over the
    ear, and the same surface carries both; laid with the side pictures (which it must be,
    or a dark strip stands down the temple from the side) the head seen from the front was
    not the front picture's. So the front picture is also kept whole (`front_layer`,
    assets/humans/web/likeness/<PERSON>_front.jpg): the square of it round the head, its
    white ground and the clothing filled from the head beside them, and beside it a block
    that says where it is shown, which is where the sheet took another picture and outside
    the face's own oval (there the sheet is the front picture already, laid on the smiling
    face), and one that says where it shows hair and where skin (it is laid on by where a
    place stands, and hair that stands behind an ear is not the ear). `texture.front` gives the renderer the picture's camera as two rows (`u`, `v`: a
    place on the grown head at rest to a place in the square) and the way it looks
    (`toward`); renderers/web/js/human-skin.js lays it on the skin by each vertex's own
    place at rest, for an eye near that line and on what faces it (FRONT_VIEW), and the
    sheet takes over as the eye moves round;
  - each iris (`read_eyes`) is read from the front picture as rings about its centre and drawn
    whole, with the colour of the whites beside it;
  - a front picture that grins shows its teeth, and its lips were being squeezed onto a mouth
    fitted shut while the side pictures, taken with the mouth shut, were laid on the same
    face. A front view marked `mouth: "open"` is a smile, and the face is fitted into it
    (`fit_smile`): MakeHuman's expression units for the mouth (axes.json `expressions`, pinned
    CC0 targets), each side of the mouth taking its own share of each, carry the lips back
    over the teeth and the corners out; what they leave, a few millimetres, is taken up in the
    picture's own plane, until the drawn lips lie on the picture's outer lip ring and the
    opening the front camera sees between them is the picture's inner ring. The rest of the
    face goes with them, as the same picture shows it: the nose's points are counted as the
    units are taken (fitted to the lips alone they carried its base a centimetre up and out,
    and the picture laid on that face showed the underside of a nose it does not show), and
    then the cheeks, the nose's wings and the lids are moved in the picture's plane onto the
    detector's points for them, smoothly. The smile is kept
    as a move of the kit's vertices (data/humans/variation/smiles/<PERSON>.json;
    tools/human_variation_kit.py carries it into the persons file): the figure rests as
    fitted, mouth shut, as the side pictures show it, and moves into the smile
    (renderers/web/js/human-variation.js gives the face the move; human-mouth.js plays it).
    Each picture is laid on the face as it was when the picture was taken: the front on the
    smiling face, the others on the face at rest. The lips take the picture's lips, never its
    teeth (`open_px`), and behind them stands a strip (`teeth_strip`: bent as the lips' inner
    edge is, set behind it, from corner to corner and a little past the lips' edges) that
    takes the picture's own pixels, opening to opening, kept as a patch in a free corner of
    the head's part of the sheet (`TEETH`). `texture.teeth` gives the renderer the strip
    (renderers/web/js/human-mouth.js adds it to the body's skin, on the head's bone);
    `texture.smile` records the units' shares, how nearly the smiling face's opening is
    the picture's, and how far the face's other points lie from the picture's, at rest and
    smiling (`face`). Where the sheet shows the mouth shut in every view, the record may name
    a picture of its own in which the person smiles (`smile_view`: the file, how far it is
    turned to set the head level, the cut round the face, the detector's points on that cut;
    `--smile PATH` hands it over). That picture is of the stand-in as they are, not of the face
    fitted to the sheet, so it is first laid on the fitted face at rest by every point a smile
    leaves alone (`SMILE_OWN`); then the smile is fitted to it and the teeth are its teeth, in
    the sheet's own light (`SMILE_TONE`). It is laid on no skin, and the front picture stays on
    the face at rest;
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
import base64
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
GROW_GRID_M = 0.002                           # ...in a solid of the pictures' outlines kept on a grid this fine
GROW_AXIS_M = 0.07                            # the hair stands out from a line this long, down from the middle between the ears' tops (the record's `grow.axis_m`, which the renderer reads)
GROW_SURE_M = (0.006, 0.014)                  # the outlines standing this far outside the bare head are hair, whatever its colour reads
BEARD_FROM_EAR_M = 0.015                      # a beard grows forward of this much in front of the ears' lobes
HAIR_SKIN_SPREAD = np.array([10.0, 4.0, 4.0])   # the least spread (L*, a*, b*) the skin's colour is given
HAIR_COLOURS = 4                              # the hair's colours are read as this many
FIT_ROUNDS = 10                               # the grown hair is then fitted to the pictures' outlines, this many times over
FIT_STEP = 0.8                                # ...each time by this share of what an outline still shows beyond it (or short of it)
FIT_REACH_M = 0.03                            # ...felt for this far, either way, along the hair's own line as the picture sees it
FIT_EDGE_M = 0.006                            # ...by the points that stand within this of the head's own outline in that picture
FIT_IN_PLANE = 0.5                            # ...whose line the picture sees at least this much of
FIT_SKIN = 0.25                               # a picture shows skin where it reads under this much hair, all round the pixel
FIT_BACK = 0.7                                # ...and hair that stands in front of skin a picture shows is drawn in to this share, each time
FIT_CELL_PX = 12                              # ...by a depth of the grown head kept on cells this wide
HAIR_GROUND = (0.86, 0.06)                    # the sheet's white ground, seen through a knot or between curls: this bright, and this near to grey
HAIR_GROWS = (0.35, 0.65)                     # hair stands out from the skin where the pictures read this much hair
HAIR_TEMPLE = 1.0                             # hair at a temple goes this far to the side pictures, where one sees it
TEMPLE_SHADE = (0.20, 0.40)                   # ...and what the front picture shows there this dark (its brightest channel) is the shade between the locks, not the hair
HAIR_FRONT_LESS = 0.8                         # past the face's width the front picture counts this much less from the ears' lobes up
HAIR_WHOLE_M = (0.002, 0.006)                 # the sheet covers hair that stands out this far, whether a picture shows it or not
GRAZE = (0.02, 0.10)                          # a texel no picture sees squarely takes the picture that sees it at all: one it faces by this much
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
SIDE_SCALE_TIE = 0.03                         # a side view's scale is held this near the front's until the views are lined up
NECK_KEEP_M = (-0.004, 0.012)                 # the head is whole from here above the chin's point
LIPS_UPPER = (191, 80, 81, 82, 13, 312, 311, 310, 415)   # MediaPipe's inner lip ring: the upper lip's edge, from the corner at the picture's left to the one at its right
LIPS_LOWER = (95, 88, 178, 87, 14, 317, 402, 318, 324)   # ...the lower lip's, the same way
LIPS_CORNERS = (78, 308)                                 # ...and the two corners between them
MOUTH_NEAR_M = 0.06                           # the mouth is drawn from the triangles within this of the lips' middle, and the inner mouth
MOUTH_BAG_UV = (0.75, 0.86, 0.93, 1.0)        # the inner mouth's own island of the body's map (u0, v0, u1, v1)
MOUTH_SHADE_U0 = 0.7545                       # ...which the renderer shades from here: the left hand's island reaches into that rectangle's near corner (human-skin.js MOUTH_SHADE)
MOUTH_PAD_PX = 24                             # ...in a window of the picture this much wider than its lips
MOUTH_ZOOM = 2                                # ...drawn at this many times the picture's size
MOUTH_HOLDS = (1.5, 4.0)                      # an open mouth is baked only where the drawn opening's edge lies within this of the picture's (mm), and the lips' outer ring within this (mm, rms)
SMILES = ROOT / 'data/humans/variation/smiles'
SMILE_FORMAT = 'chicago4d_human_smile_v1'
SMILE_UNIT_M = 1e-5                           # a smile's moves are kept in the kit's own delta unit
SMILE_MOST = 1.25                             # neither side of the mouth takes more than this much of an expression unit
SMILE_RIDGE_MM = 0.25                         # ...and a unit taken whole costs as much as this miss on every point of the lips
SMILE_SIDE_M = 0.008                          # the two sides share a unit across this much of the midline, each way
SMILE_ROUNDS = 4                              # the drawn opening's edge is read again this many times
SMILE_REST_M = (0.022, 0.034)                 # what the units leave is taken up in the picture's plane this near the lips, fading out between the two
SMILE_NEAR_M = (0.05, 0.065)                  # ...and this near them in depth (the back of the head lies behind them in the picture)
SMILE_DROP_M = 5e-5                           # a vertex the smile moves less than this is left out of its record
SMILE_NOSE = 0.5                              # as the units are taken, a point of the nose counts this much of a point of the lips
SMILE_NOSE_M = (0.026, 0.004)                 # ...the nose being the face's points within this of the midline, from this far under the nose's base up to the nasion
SMILE_FACE_SMOOTH = 300.0                     # the rest of the face follows its points in the picture this smoothly (a thin-plate spline's smoothing, pixels)
SMILE_FACE_M = (0.008, 0.022)                 # ...where the skin is this near one of them, fading out between the two
SMILE_EYE_M = (0.016, 0.024)                  # ...and skin this near an eye's middle keeps its distance from it (the lids stay on the eye)
SMILE_FACE_HOLDS_MM = 2.5                     # a smile is baked only where the face's other points end within this of the picture's (mm, rms)
SMILE_TONE = {'in_m': 0.0035, 'out_m': 0.015, 'most': 2.0}   # a smile picture of its own: its teeth take the sheet's light by the skin round the lips, from this far out from them to this far (metres, the same skin in both pictures), each channel by no more than this
SMILE_OWN = {'mouth_m': 0.010, 'smooth': 300.0, 'step_px': 8,   # ...and it is laid on the fitted face by every point further than this from its lips, this smoothly (a thin-plate spline's smoothing, pixels), worked out every so many pixels
             'settle_px': 0.01, 'rounds': 60}                  # ...each point followed to where its pixel went until it moves less than this, in no more rounds than this
FRONT = {'px': 512, 'alpha_px': 128,           # the front picture, kept for the renderer to show from the front: the head's square of it at this size, and beside it where it is shown
         'pad_px': 10,                         # ...the square standing this far outside the head's outline (the picture's pixels)
         'face_in_px': 12,                     # ...shown outside the face's own outline drawn in by this much (inside it the sheet is the front picture already, laid on the smiling face)
         'soft_px': 2.0,                       # ...its edge this soft
         'outline_in_px': 6,                   # ...and the picture's own pixels taken from this far inside the head's outline (its blur into the white ground)
         'rim_px': 16, 'rim_pale': 0.62,       # ...nothing this pale (its darkest channel) within this far of the outline
         'mirror_px': 24}                      # ...and past them the picture mirrored in their edge for this far, their nearest colour beyond
FRONT_OVAL = (10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377,
              152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109)   # MediaPipe: the face's outline
TEETH = {'px': (444, 0, 508, 160),            # the teeth's patch: a free corner of the head's part of the sheet
         'grid': (17, 5),                     # the strip behind the lips: points across and down
         'back_m': 0.0025,                    # ...set back this far behind the lips' inner edge
         'over_m': (0.003, 0.002, 0.002),     # ...standing this far above that edge, below it and past its corners
         'pad_px': 8,                         # the patch keeps this much of the picture round the strip's own pixels
         'shown': 0.9}                        # ...and the front camera must see the strip, not the inner mouth, in this share of the opening


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


FINE_EDGE_M = 0.008                           # the head's triangles are split until none of theirs is longer than this
FINE_REACH_M = 0.17                           # ...within this of the middle between the ears' tops
FINE_ROUNDS = 3
FINE_CELL_PX = 16                             # where the hair stands out, kept for the renderer as cells of the sheet this wide
FINE_STAND_M = 0.002                          # ...a cell counts where the hair stands out this far in it


def refine(X, rest, uv, tri, lm):
    """The head's skin finer: its triangles within `FINE_REACH_M` of the middle between the
    ears' tops are split in four until no edge of theirs is longer than `FINE_EDGE_M` (the
    scalp's are 13 to 35 mm, too coarse to carry a knot's or a curl's outline), and whatever
    borders a split triangle is split along the shared edge, so no seam opens. A new vertex is
    the middle of its edge in every attribute; the vertices that were there keep their rows.
    renderers/web/js/human-fine.js splits the body's own skin the same way where the sheet
    says hair stands out (`texture.grow.fine`), so the app's head carries what is baked here."""
    mid = (X[lm['ear_top_l']] + X[lm['ear_top_r']]) / 2
    splits = []
    for _ in range(FINE_ROUNDS):
        group = weld(rest)
        e = np.stack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]], 1)                 # (triangle, edge, end)
        length = np.linalg.norm(X[e[:, :, 0]] - X[e[:, :, 1]], axis=2)
        near = np.linalg.norm(X[tri].mean(1) - mid, axis=1) < FINE_REACH_M
        whole = near & (length.max(1) > FINE_EDGE_M)
        if not whole.any():
            break
        key = np.sort(group[e], 2)
        key = key[:, :, 0].astype(np.int64) * len(X) + key[:, :, 1]
        marked = np.isin(key, np.unique(key[whole]))                                      # by place, so both sides of a UV seam split
        pair = np.sort(e, 2)
        pk = pair[:, :, 0].astype(np.int64) * len(X) + pair[:, :, 1]
        uniq, first = np.unique(pk[marked], return_index=True)
        ends = pair[marked][first]
        new = len(X) + np.arange(len(uniq))
        X = np.concatenate([X, (X[ends[:, 0]] + X[ends[:, 1]]) / 2])
        rest = np.concatenate([rest, (rest[ends[:, 0]] + rest[ends[:, 1]]) / 2])
        uv = np.concatenate([uv, (uv[ends[:, 0]] + uv[ends[:, 1]]) / 2])
        splits.append(ends)
        m = np.full(pk.shape, -1)
        m[marked] = new[np.searchsorted(uniq, pk[marked])]
        out = [tri[~marked.any(1)]]
        for t, mm in zip(tri[marked.any(1)], m[marked.any(1)]):
            n = int((mm >= 0).sum())
            if n == 3:
                out.append(np.array([[t[0], mm[0], mm[2]], [mm[0], t[1], mm[1]], [mm[2], mm[1], t[2]], [mm[0], mm[1], mm[2]]]))
                continue
            k = int(np.argmax(mm >= 0)) if n == 1 else int(np.argmax(mm < 0))            # the one edge split, or the one not
            a, b, c = t[k], t[(k + 1) % 3], t[(k + 2) % 3]
            if n == 1:
                out.append(np.array([[a, mm[k], c], [mm[k], b, c]]))
            else:
                mb, mc = mm[(k + 1) % 3], mm[(k + 2) % 3]                                 # on b-c and on c-a; a-b is whole
                out.append(np.array([[c, mc, mb], [mc, a, b], [mc, b, mb]]))
        tri = np.concatenate(out)
    return X, rest, uv, tri, splits


def fitted_head(person):
    """The body's skin with the person's fitted face on it (metres): the kit's vertices in the
    kit's order (`kit_n` of them), then the vertices `refine` adds to the head (`splits`: the
    two ends each was the middle of, a round at a time)."""
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
    lm = {k: kidx[v] for k, v in F.landmarks().items() if isinstance(v, int)}
    tri, uv = F.body_triangles(asset), glb_attribute(asset, 'TEXCOORD_0')
    kit_n, splits = len(rest), []
    if FINE_EDGE_M:
        X, rest, uv, tri, splits = refine(X, rest, uv, tri, lm)
    return {'X': X, 'rest': rest, 'tri': tri, 'uv': uv, 'asset': asset, 'person': person, 'kit_n': kit_n, 'splits': splits,
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


def mirror_fill(img, hole, known, reach=None):
    """`hole` pixels of img filled with the known ones' own grain: each takes the known pixel
    that lies as far past the nearest known one as it lies short of it (the picture mirrored in
    the hole's edge), or that nearest one where the mirrored place is not known (or the hole's
    edge is more than `reach` pixels off), and the seam is smoothed a little, among the known
    and the filled pixels alone (whatever else lies beside them, an island's unwritten edge,
    stays out of it). Hair no picture shows (the underside of a beard) is then hair, with the
    curl of the hair beside it, where the nearest colours drawn out and blurred were a smear."""
    from scipy import ndimage
    H, W = hole.shape
    far, idx = ndimage.distance_transform_edt(~known, return_indices=True)
    ys, xs = np.nonzero(hole)
    by, bx = idx[0][ys, xs], idx[1][ys, xs]
    my, mx = np.clip(2 * by - ys, 0, H - 1), np.clip(2 * bx - xs, 0, W - 1)
    ok = known[my, mx] & (far[ys, xs] <= (reach if reach is not None else np.inf))
    out = img.copy()
    out[ys, xs] = np.where(ok[:, None], img[my, mx], img[by, bx])
    own = (known | hole).astype(np.float32)
    share = np.maximum(ndimage.uniform_filter(own, 3), 1e-6)[:, :, None]
    for _ in range(2):
        blur = np.stack([ndimage.uniform_filter(out[:, :, c] * own, 3) for c in range(out.shape[2])], -1) / share
        out[hole] = blur[hole]
    return out


def side_camera(head, T, pts, fg, turn_deg, centre, size, scale, lower='menton'):
    """A side view's camera: its near-side points, and the face's line against the white ground
    matched by the head's own outline from that side (closest points, re-found each pass). The
    line runs from the brow down to `lower`: the chin's point, or the nose's base for a face
    with a beard (a beard's outline is not the jaw's: matched to it, the head tipped ten degrees
    and the ears sat a centimetre low). The turn starts as the fit's own side view's (the
    record's by eye where there is none) and the scale near the front's; both are loosely held
    by a line this short, and `line_up` settles them against the other views. Returns the
    camera, its mean miss on the line (mm), and what it was solved on."""
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
        rows = rows[(X[rows, 2] > ear_z + 0.03) & (X[rows, 1] < X[mp[168], 1] + 0.065) & (X[rows, 1] > X[lm[lower], 1] - 0.005)]
        d, j = cKDTree(E).query(Pm[rows])
        rows, target = rows[d < 14], E[j[d < 14]]
        w = np.sqrt(120.0 / max(len(rows), 1))

        def res(q):
            c = np.concatenate([[turn], q])
            a = (project(P, c, centre)[0] - ob) / 6.0
            b = (project(X[rows], c, centre)[0] - target) * w / 2.0
            return np.concatenate([np.tanh(a.ravel() / 3) * 3, b.ravel(), [(c[3] / scale - 1) / SIDE_SCALE_TIE * 3]])
        cam = np.concatenate([[turn], least_squares(res, cam[1:], x_scale='jac').x])
    miss = np.linalg.norm(project(X[rows], cam, centre)[0] - target, axis=1).mean() / cam[3] * 1000
    return cam, float(miss), {'rows': rows, 'edge': E}


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
        v = {'name': spec['name'], 'img': img, 'fg': fg, 'size': size, 'pts': pts, 'mouth': spec.get('mouth')}
        if spec['name'] == 'front':
            use = [i for i in idx if spec.get('camera') != 'upper_face' or X[mp[i], 1] > X[lm['subnasale'], 1] + 0.004]
            v['cam'] = solve_camera(X[[mp[i] for i in use]], pts[use], centre, (-0.3, 0.0, 0.3))
            v['miss_mm'] = float(np.sqrt(((project(X[[mp[i] for i in use]], v['cam'], centre)[0] - pts[use]) ** 2).sum(1).mean()) / v['cam'][3] * 1000)
            v['fit'] = {'rows': np.array([mp[i] for i in use]), 'at': pts[use]}
        elif spec['name'] == 'back':
            v['cam'] = np.array([np.pi, 0.0, 0.0, np.mean([w['cam'][3] for w in views if w['name'] in ('left', 'right')]), 0.0, 0.0])
        else:
            # A side view is turned as the fit placed its own side view (the face was shaped to
            # match the picture from there); with no such fit, as the record reads it by eye.
            turn = np.copysign(head['side_turn_deg'] or abs(spec['turn_deg']), spec['turn_deg'])
            v['cam'], v['miss_mm'], v['fit'] = side_camera(head, T, pts, fg, turn, centre, size, views[0]['cam'][3],
                                                           'subnasale' if (rec.get('grow') or {}).get('beard') else 'menton')
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
    if len(views) > 2 and rec.get('line_up', True):
        line_up(views, X, np.unique(T), lm, centre, (rec.get('grow') or {}).get('max_cm', 8) / 100)
    return views, T, centre, xmid


def smile_picture(spec, path):
    """A record's own picture of the person smiling (`smile_view`), as the tool reads it: turned
    `level_deg` so the head is level in it, and cut to `crop_px` of the turned picture."""
    from PIL import Image
    return Image.open(path).convert('RGB').rotate(spec['level_deg'], resample=Image.BICUBIC, expand=True).crop(tuple(spec['crop_px']))


def read_smile_view(rec, path, head, centre):
    """The record's `smile_view` as a view: its picture, the detector's points on it and its
    camera, found on the points the smile does not move (the front view's own rule), or None
    where the record names none. The picture comes back laid on the fitted face (SMILE_OWN)."""
    spec = rec.get('smile_view')
    if not spec:
        return None
    if not path:
        sys.exit(f"{rec['person_id']}: the record names a picture of the smile; hand it over with --smile")
    if sha256(path) != spec['sha256']:
        sys.exit(f"{rec['person_id']}: {path} is not the smile's picture the record names (SHA-256 differs)")
    from PIL import Image, ImageDraw
    from scipy import ndimage
    from scipy.interpolate import RBFInterpolator
    X, mp, lm = head['X'], head['mp'], head['lm']
    img = np.asarray(smile_picture(spec, path)).astype(np.float32) / 255
    H, W = img.shape[:2]
    pts = np.asarray(spec['points_px'], float)
    idx = sorted(mp)
    use = [i for i in idx if spec.get('camera') != 'upper_face' or X[mp[i], 1] > X[lm['subnasale'], 1] + 0.004]
    cam = solve_camera(X[[mp[i] for i in use]], pts[use], centre, (-0.3, 0.0, 0.3))
    miss = float(np.sqrt(((project(X[[mp[i] for i in use]], cam, centre)[0] - pts[use]) ** 2).sum(1).mean()) / cam[3] * 1000)
    # The picture is of the stand-in as they are, and the face was fitted to the sheet: between
    # the two the chin stands some millimetres lower and to one side, and fitted to that the
    # smile came out lopsided, with a crease down one cheek. So the picture is first laid on
    # the fitted face at rest by every point a smile leaves where it was (all but the lips'
    # own neighbourhood), smoothly; what is left between the two is the smile.
    im = Image.new('L', (W, H), 0)
    ImageDraw.Draw(im).polygon([tuple(q) for q in pts[list(LIPS)]], fill=1)
    by_mouth = ndimage.distance_transform_edt(~np.asarray(im, bool)) <= SMILE_OWN['mouth_m'] * cam[3]
    still = [i for i in idx if not by_mouth[int(np.clip(pts[i, 1], 0, H - 1)), int(np.clip(pts[i, 0], 0, W - 1))]]
    P = project(X[[mp[i] for i in still]], cam, centre)[0]
    back = RBFInterpolator(P, pts[still] - P, kernel='thin_plate_spline', smoothing=SMILE_OWN['smooth'])
    step = SMILE_OWN['step_px']
    gy, gx = np.mgrid[0:H + step:step, 0:W + step:step]
    coarse = back(np.stack([gx.ravel(), gy.ravel()], 1).astype(float)).reshape(*gx.shape, 2).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    at = np.stack([xx.ravel() + 0.5, yy.ravel() + 0.5], 1)
    shift = sample(coarse, at / step + 0.5)
    laid = sample(img, at + shift).reshape(H, W, 3).astype(np.float32)
    # ...and each of the detector's points to where its pixel went.
    moved = pts.copy()
    for _ in range(SMILE_OWN['rounds']):
        last, moved = moved, pts - back(moved)
        if np.abs(moved - last).max() < SMILE_OWN['settle_px']:
            break
    else:
        sys.exit(f"{rec['person_id']}: the smile's picture lies too far from the fitted face to be laid on it (its points do not settle)")
    off = np.linalg.norm(pts[still] - P, axis=1) / cam[3] * 1000
    return {'name': 'smile', 'img': laid, 'size': (W, H), 'pts': moved, 'cam': cam, 'miss_mm': miss, 'mouth': 'open',
            'laid_on': {'points': len(still), 'off_mm': round(float(np.sqrt((off ** 2).mean())), 2), 'most_mm': round(float(np.linalg.norm(moved - pts, axis=1).max() / cam[3] * 1000), 2)}}


def smile_tone(sv, front):
    """What each channel of a smile picture is multiplied by to stand in the sheet's light: the
    skin round the lips in the front picture over the same skin in the smile's (linear light,
    SMILE_TONE)."""
    from PIL import Image, ImageDraw
    from scipy import ndimage

    def ring(v):
        im = Image.new('L', v['size'], 0)
        ImageDraw.Draw(im).polygon([tuple(q) for q in v['pts'][list(LIPS)]], fill=1)
        far = ndimage.distance_transform_edt(~np.asarray(im, bool)) / v['cam'][3]
        m = (far > SMILE_TONE['in_m']) & (far <= SMILE_TONE['out_m'])
        return srgb_to_linear(v['img'][m]).mean(0)

    return np.clip(ring(front) / np.maximum(ring(sv), 1e-4), 1 / SMILE_TONE['most'], SMILE_TONE['most'])


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
    head['tones'] = None
    if len(hair_px) < 200:
        return np.zeros(len(X)), {'skin_lab': [round(float(c), 1) for c in mu], 'hair_px': int(len(hair_px))}
    cen, _ = kmeans2(hair_px[::max(1, len(hair_px) // 20000)], HAIR_COLOURS, minit='++', seed=7)
    head['tones'] = (mu, sd, cen)
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


def away(X, mid):
    """Which way the hair stands out from each point of the skin: from the head's upright middle
    line (from the ears' tops `GROW_AXIS_M` down), so the crown's hair rises, the hair at the
    back and sides stands straight out, and a beard and the hair on the neck stand out and down.
    renderers/web/js/human-skin.js moves the skin the same way (`chiLikeAxis`, the record's `axis_m`)."""
    o = np.stack([np.full(len(X), mid[0]), np.clip(X[:, 1], mid[1] - GROW_AXIS_M, mid[1]), np.full(len(X), mid[2])], 1)
    U = X - o
    return U / np.maximum(np.linalg.norm(U, axis=1, keepdims=True), 1e-9)


def outline_holds(masks, cams, centre, lo, shape):
    """The points inside every view's outline (a grid of `GROW_GRID_M`)."""
    ax = [lo[c] + GROW_GRID_M * np.arange(shape[c]) for c in range(3)]
    gx, gy, gz = np.meshgrid(*ax, indexing='ij')
    pts = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], 1)
    occ = np.ones(len(pts), bool)
    for m, cam in zip(masks, cams):
        H, W = m.shape
        P = project(pts, cam, centre)[0]
        xi, yi = np.floor(P[:, 0]).astype(int), np.floor(P[:, 1]).astype(int)
        occ &= (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H) & m[np.clip(yi, 0, H - 1), np.clip(xi, 0, W - 1)]
    return occ.reshape(shape)


def rounded(occ):
    """The solid the outlines allow: what `outline_holds`, each level slice of it rounded to the
    ellipse its extent holds (four views leave a slice its corners; a head and its hair have none)."""
    from scipy import ndimage
    shape = occ.shape
    solid = np.zeros_like(occ)
    ix, iz = np.arange(shape[0])[:, None], np.arange(shape[2])[None, :]
    for j in range(shape[1]):
        lab, n = ndimage.label(occ[:, j, :])
        for k, sl in enumerate(ndimage.find_objects(lab), 1):
            a, b = (sl[0].stop - sl[0].start) / 2, (sl[1].stop - sl[1].start) / 2
            cx, cz = (sl[0].start + sl[0].stop - 1) / 2, (sl[1].start + sl[1].stop - 1) / 2
            solid[:, j, :] |= (lab == k) & (((ix - cx) / a) ** 2 + ((iz - cz) / b) ** 2 <= 1)
    return solid


def leaves(solid, lo, P, U, most):
    """How far along its line each point goes before it leaves the solid (0 for one outside it)."""
    steps = np.arange(0, most + GROW_STEP_M / 2, GROW_STEP_M)
    shape = np.array(solid.shape)
    out = np.zeros(len(P))
    for a in range(0, len(P), 2000):
        p = P[a:a + 2000, None, :] + steps[None, :, None] * U[a:a + 2000, None, :]
        i = np.round((p - lo) / GROW_GRID_M).astype(int)
        ok = ((i >= 0) & (i < shape)).all(2)
        i = np.clip(i, 0, shape - 1)
        inside = ok & solid[i[..., 0], i[..., 1], i[..., 2]]
        first = np.where(inside.all(1), len(steps), np.argmin(inside, 1))
        out[a:a + 2000] = steps[np.maximum(first - 1, 0)]
    return out


LINE_UP_GRID_M = 0.003
LINE_UP_SMALLER = 3
LINE_UP_STEP = np.array([2.0, 2.0, 2.0, 1.0, 2.0, 2.0])       # a camera's turn, tilt and roll (degrees), scale (percent), and place across and down (mm): the first steps tried
LINE_UP_HOLD = np.array([0.02, 0.02, 0.02, 0.1, 0.02, 0.02])  # what a unit of each, squared, costs (cm2 of outline)
LINE_UP_FIT = 10.0                                             # ...and a millimetre more of miss on what the camera was solved on


def moved(cam, d):
    """A camera turned, tilted and rolled by d[0:3] degrees, its scale changed by d[3] percent,
    and its picture's place by d[4:6] mm."""
    c = np.array(cam, float)
    c[:3] += np.radians(d[:3])
    c[3] *= 1 + d[3] / 100
    c[4:6] += d[4:6] / 1000 * cam[3]
    return c


def line_up(views, X, hv, lm, centre, most):
    """The cameras together. Each was solved on its own picture: the front's on the face's
    points, which hardly say how far the head is tilted to or from the camera; a side's on the
    face's line; the back's by rule (it has no face). So the hair's outline, which every view
    shows, sat a few degrees and millimetres apart between them, and the solid all four
    outlines allow lost whatever any one disagreed on (a top knot lost its top 2 cm). Here the
    cameras are moved together until that solid shadows as much of every outline as it can. A
    move costs what it loses of the fit the camera was solved on (`LINE_UP_FIT` a millimetre)
    and a little besides (`LINE_UP_HOLD`), so a camera its own picture places firmly stays
    and one it places loosely gives. Changes `v['cam']` in place, and notes the move, and the
    outlines' area above the chin left unshadowed before and after (cm2 a view)."""
    from scipy import ndimage
    from scipy.spatial import cKDTree
    g, q = LINE_UP_GRID_M, LINE_UP_SMALLER
    lo = X[hv].min(0) - most - g
    shape = np.ceil((X[hv].max(0) + most + g - lo) / g).astype(int) + 1
    pts = np.stack([a.ravel() for a in np.meshgrid(*[lo[c] + g * np.arange(shape[c]) for c in range(3)], indexing='ij')], 1)
    floor = X[lm['menton'], 1] - 0.01                      # above the chin: the collar's line differs view to view
    pts = pts[pts[:, 1] > floor - 0.03]
    n = len(views)
    cam0 = [np.array(v['cam'], float) for v in views]
    masks, counted, fits = [], [], []
    for v, c in zip(views, cam0):
        m = v['head']
        H, W = m.shape
        small = m[:H // q * q, :W // q * q].reshape(H // q, q, W // q, q).mean((1, 3)) > 0.5
        above = np.zeros(small.shape, bool)
        above[:max(1, int((c[5] - c[3] * (floor - centre[1])) / q) - 2)] = True
        masks.append(small)
        counted.append(small & above)
        f = v.get('fit')
        fits.append(None if f is None else ('points', f['rows'], f['at']) if 'at' in f else ('outline', f['rows'], cKDTree(f['edge'])))
    # only the points the first outline could come to hold
    P = project(pts, cam0[0], centre)[0] / q
    wide = ndimage.binary_dilation(masks[0], iterations=int(np.ceil(0.02 * cam0[0][3] / q)))
    xi, yi = np.floor(P[:, 0]).astype(int), np.floor(P[:, 1]).astype(int)
    ok = (xi >= 0) & (xi < wide.shape[1]) & (yi >= 0) & (yi < wide.shape[0])
    pts = pts[ok & wide[np.clip(yi, 0, wide.shape[0] - 1), np.clip(xi, 0, wide.shape[1] - 1)]]

    def seen(i, c):
        m = masks[i]
        P = project(pts, c, centre)[0] / q
        xi, yi = np.floor(P[:, 0]).astype(int), np.floor(P[:, 1]).astype(int)
        ok = (xi >= 0) & (xi < m.shape[1]) & (yi >= 0) & (yi < m.shape[0])
        xi, yi = np.clip(xi, 0, m.shape[1] - 1), np.clip(yi, 0, m.shape[0] - 1)
        return xi, yi, ok & m[yi, xi]

    def miss(i, c):
        """How far the camera is from what it was solved on, mm."""
        if fits[i] is None:
            return 0.0
        kind, rows, at = fits[i]
        P = project(X[rows], c, centre)[0]
        if kind == 'points':
            return float(np.sqrt(((P - at) ** 2).sum(1).mean()) / c[3] * 1000)
        return float(np.minimum(at.query(P)[0], 14.0).mean() / c[3] * 1000)

    def missed(pix):
        inside = np.ones(len(pts), bool)
        for x, y, on in pix:
            inside &= on
        out = []
        for i, (x, y, on) in enumerate(pix):
            sh = np.zeros(masks[i].shape, bool)
            sh[y[inside], x[inside]] = True
            sh = ndimage.binary_closing(sh, iterations=2)
            out.append((counted[i] & ~sh).sum() / (cam0[i][3] / q) ** 2 * 1e4)
        return np.array(out)

    miss0 = [miss(i, cam0[i]) for i in range(n)]
    pix = [seen(i, cam0[i]) for i in range(n)]
    before = missed(pix)
    d = np.zeros((n, len(LINE_UP_STEP)))
    price = lambda i, di, c: LINE_UP_FIT * (miss(i, c) - miss0[i]) + float(LINE_UP_HOLD @ di ** 2)
    prices = [0.0] * n
    best = float(before.sum())
    step = np.tile(LINE_UP_STEP, (n, 1)).astype(float)
    # A pattern search (the cost is a count of pixels, so it has no slope to follow): each
    # move in turn is tried a step either way and the better kept; when none helps the steps halve.
    while (step > LINE_UP_STEP / 16 + 1e-12).any():
        better = False
        for i in range(n):
            for k in range(d.shape[1]):
                for sgn in (1.0, -1.0):
                    di = d[i].copy()
                    di[k] += sgn * step[i, k]
                    c = moved(cam0[i], di)
                    trial = pix[:i] + [seen(i, c)] + pix[i + 1:]
                    pr = price(i, di, c)
                    cost = float(missed(trial).sum()) + sum(prices) - prices[i] + pr
                    if cost < best - 1e-9:
                        d[i], pix, prices[i], best, better = di, trial, pr, cost, True
                        break
        if not better:
            step /= 2
    after = missed(pix)
    for i, v in enumerate(views):
        c = moved(cam0[i], d[i])
        v['cam'] = c
        v['lined_up'] = {'moved': [round(float(a), 2) for a in d[i]], 'unshadowed_cm2': [round(float(before[i]), 1), round(float(after[i]), 1)],
                         **({'miss_mm': [round(miss0[i], 2), round(miss(i, c), 2)]} if fits[i] is not None else {})}
    return d, before, after


def filled(P, tri, size):
    """The outline of triangles `tri` of the pixel points P, filled: a (H, W) mask."""
    from PIL import Image, ImageDraw
    im = Image.new('1', size, 0)
    draw = ImageDraw.Draw(im)
    for q in P[tri].reshape(-1, 6).tolist():
        draw.polygon(q, fill=1)
    return np.asarray(im, bool)


def reads_skin(views, tones):
    """Where each picture shows bare skin (not hair, clothing or its ground): by the tones
    `hair_shown` read, with no hair within two pixels."""
    from scipy import ndimage
    mu, sd, cen = tones
    out = []
    for v in views:
        H, W = v['fg'].shape
        lab = to_lab(np.stack([ndimage.gaussian_filter(v['img'][:, :, c], 1.5) for c in range(3)], -1).reshape(-1, 3))
        ds = (((lab - mu) / sd) ** 2).sum(1)
        dh = (((lab[:, None, :] - cen[None]) / sd) ** 2).sum(2).min(1)
        r = np.where(v['good'].ravel() > 0.5, ds / np.maximum(ds + dh, 1e-9), 1.0).reshape(H, W)
        out.append(ndimage.maximum_filter(r, 5) < FIT_SKIN)
    return out


def fit_outlines(t, Xg, U, Tg, views, centre, free, sides_only, limit, A, deg, skin=None):
    """The grown hair fitted to the pictures' outlines. The solids `grow` measures in are what
    four outlines allow, less what they allow the bare head, and that falls short where the bare
    head's own solid is loose (behind the ears, whose width it carries back along the skull)
    and wherever the mesh cannot reach. So the head is drawn again as each picture's camera
    sees it, hair and all, and each point that stands on its outline there (and whose line the
    camera sees) is moved along its line by what the picture's outline shows beyond it, or
    back by what it stands outside; a point takes the least any picture gives it, its
    neighbours follow, and `limit` (the caps and the rise from the hair's edge) holds
    throughout. Only `free` points move; `sides_only` ones are fitted to the side pictures
    alone (in front of the ears a front or back picture's width is hair that hangs behind them).
    And inside the outlines: hair that stands, nearest a camera, where its picture shows bare
    skin (`skin`: an ear, the neck under it) is drawn in until it no longer covers it. Curls
    that hang clear of a neck are, on this skin, a bank standing from it; drawn in so, the
    bank's face lies along the side picture's own line of sight and faces the front picture."""
    from scipy import ndimage
    for _ in range(FIT_ROUNDS):
        Xc = Xg + U * t[:, None]
        gap = np.full(len(Xg), np.inf)
        covers = np.zeros(len(Xg), bool)
        for i, v in enumerate(views):
            W, H = v['size']
            s = v['cam'][3]
            P, z = project(Xc, v['cam'], centre)
            if skin is not None:
                xi, yi = np.floor(P[:, 0]).astype(int), np.floor(P[:, 1]).astype(int)
                on = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
                xi, yi = np.clip(xi, 0, W - 1), np.clip(yi, 0, H - 1)
                wc = W // FIT_CELL_PX + 1
                cell = (yi // FIT_CELL_PX) * wc + xi // FIT_CELL_PX
                near = np.full((H // FIT_CELL_PX + 1) * wc, -np.inf)
                np.maximum.at(near, cell[on], z[on])
                near = ndimage.maximum_filter(near.reshape(-1, wc), 3).ravel()
                covers |= free & on & (t > 0.002) & (z > near[cell] - 0.012) & skin[i][yi, xi]
            D = project(Xc + U * 0.01, v['cam'], centre)[0] - P
            n = np.linalg.norm(D, axis=1)
            seen = n / (0.01 * s)
            ok = free & (seen > FIT_IN_PLANE)
            if v['name'] in ('front', 'back'):
                ok &= ~sides_only
            k = np.nonzero(ok)[0]
            if not len(k):
                continue
            mesh = filled(P, Tg, (W, H))
            d = D[k] / n[k, None]
            js = np.arange(int(np.ceil(FIT_REACH_M * s)) + 1)

            def first(mask, sign, want):
                q = P[k, None, :] + sign * d[:, None, :] * js[None, :, None]
                xi, yi = np.floor(q[..., 0]).astype(int), np.floor(q[..., 1]).astype(int)
                hit = ((xi >= 0) & (xi < W) & (yi >= 0) & (yi < H) & mask[np.clip(yi, 0, H - 1), np.clip(xi, 0, W - 1)]) == want
                return np.where(hit.any(1), np.argmax(hit, 1), len(js))

            mesh_out = first(mesh, 1, False)
            xi, yi = np.clip(np.floor(P[k, 0]).astype(int), 0, W - 1), np.clip(np.floor(P[k, 1]).astype(int), 0, H - 1)
            on_head, on_figure = v['head'][yi, xi], v['fg'][yi, xi]
            px = np.where(on_head, first(v['head'], 1, False) - mesh_out, np.where(on_figure, 0, -first(v['fg'], -1, True))).astype(float)
            use = (mesh_out <= FIT_EDGE_M * s) & (on_head | ~on_figure)
            g = px / (s * seen[k])
            gap[k[use]] = np.minimum(gap[k[use]], g[use])
        has = np.isfinite(gap)
        if not has.any() and not covers.any():
            break
        d_, w_ = np.where(has, np.clip(gap, -0.015, 0.015), 0.0), has.astype(float)
        for _ in range(2):
            d_, w_ = 0.5 * d_ + 0.5 * (A @ d_) / deg, 0.5 * w_ + 0.5 * (A @ w_) / deg
        t = np.clip(t + FIT_STEP * np.where(free & ~covers, d_ / np.maximum(w_, 0.5), 0.0), 0, limit)
        t[covers] *= FIT_BACK
    return t


def grow(rec, views, head, T, centre):
    """How far the stand-in's hair (and a beard) stands out from the fitted skin: a distance for
    each vertex of the head (the finer one's), metres, along `away`, and the middle `away` is measured from.
    The pictures give it. Their four outlines allow one solid (`outline_holds`, `rounded`: the figure down
    to the collar); the bare fitted head, seen by the same four cameras, allows another, made
    the same way; a point of the skin leaves the head's own solid after one distance along its
    line and the pictures' after another, and the difference is the hair's depth there (the two
    solids are built alike, so what four views cannot tell of a shape is taken off both). It
    grows only where the pictures show hair, not on the face, the lips or the ears, no faster
    from the hair's edge than `rise`, and is smoothed a little; then it is fitted to the
    pictures' own outlines (`fit_outlines`; `fit: false` in the record leaves that out), and a
    point off the sheet stays where it is. With no `grow` in the record nothing is grown."""
    from scipy import sparse
    from scipy.sparse.csgraph import dijkstra
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
    U = away(Xg, mid)
    most = spec['max_cm'] / 100
    lo = X[hv].min(0) - most - GROW_GRID_M
    shape = tuple(np.ceil((X[hv].max(0) + most + GROW_GRID_M - lo) / GROW_GRID_M).astype(int) + 1)
    cams = [v['cam'] for v in views]
    own = []
    for v in views:
        P, z = project(X, v['cam'], centre)
        own.append(raster(P, z, T, v['size'])[1] >= 0)
    held = outline_holds(own, cams, centre, lo, shape)
    in_bare = leaves(rounded(held), lo, Xg, U, most)
    t = np.clip(leaves(rounded(outline_holds([v['head'] for v in views], cams, centre, lo, shape)), lo, Xg, U, most) - in_bare, 0, None)
    # In front of the ears and below their tops, four views cannot say where a width is: hair
    # that hangs behind the ears widens the front and back pictures beside the jaw, and the
    # solid above lays that width on the cheeks too. For a record with `cheek_cm` the face there
    # is measured in a second solid: the side pictures' outlines whole, the front and back
    # pictures' no wider than the bare head's own a `cheek_cm` out (and as far down as a beard
    # hangs), and behind the ears the bare head itself. The hair there is no deeper than that.
    low, ahead = np.zeros(G), np.zeros(G)
    if spec.get('cheek_cm') is not None:
        from scipy import ndimage
        ears_z = max(X[lm[k], 2] for k in ('ear_top_l', 'ear_top_r', 'ear_lobe_l', 'ear_lobe_r'))
        tops_y = min(X[lm['ear_top_l'], 1], X[lm['ear_top_r'], 1])
        narrow = []
        for v, o in zip(views, own):
            if v['name'] in ('front', 'back'):
                bx, by = (max(1, int(round(c / 100 * v['cam'][3]))) for c in (spec['cheek_cm'], spec.get('beard_cm', 1.5)))
                narrow.append(v['head'] & ndimage.binary_dilation(o, structure=np.ones((2 * by + 1, 2 * bx + 1), bool)))
            else:
                narrow.append(v['head'])
        face = outline_holds(narrow, cams, centre, lo, shape)
        k = int(np.ceil((ears_z - lo[2]) / GROW_GRID_M))
        face[:, :, :k] = held[:, :, :k]
        ahead = smooth(ears_z, ears_z + 0.01, Xg[:, 2])
        low = ahead * (1 - smooth(tops_y - 0.015, tops_y, Xg[:, 1]))
        t -= low * np.clip(t - np.clip(leaves(rounded(face), lo, Xg, U, most) - in_bare, 0, None), 0, None)
    # Only where the pictures show hair: skin does not stand out from itself.
    hair = np.zeros(G)
    np.maximum.at(hair, gi, head['hair'][hv])
    # ...or where the pictures' solid stands so far outside the head's own that only hair can be
    # there (grey hair is the skin's own colour to the reading above).
    # (Not in front of the ears, for a record with `cheek_cm`: a temple the side pictures show
    # bare stood out with the hair that is swept back over the ear behind it.)
    shown = np.maximum(smooth(HAIR_GROWS[0], HAIR_GROWS[1], hair), smooth(GROW_SURE_M[0], GROW_SURE_M[1], t) * (1 - ahead))
    if spec.get('beard'):
        # ...and a beard, where the lower face reads as hair, no deeper than the record gives it.
        # (Grey stubble on a cheek reads as skin and stays the skin's: it is a few millimetres deep,
        # and made to stand out wherever the outlines allowed, it stood as a shelf beside the mouth.)
        lobes_z = max(X[lm['ear_lobe_l'], 2], X[lm['ear_lobe_r'], 2])
        beard = (Xg[:, 1] < X[lm['subnasale'], 1] - 0.002) & (Xg[:, 2] > lobes_z + BEARD_FROM_EAR_M)
        t = np.where(beard, np.minimum(t, spec.get('beard_cm', 1.5) / 100), t)
    t = t * shown
    # Nothing grows on the face (inside the points MediaPipe reads on it), the lips, or the ears.
    front = next(v for v in views if v['name'] == 'front')
    Pf = project(Xg, front['cam'], centre)[0]
    idx = sorted(mp)
    R = Xg - mid
    face = inside_hull(project(X[[mp[i] for i in idx]], front['cam'], centre)[0], Pf) & (R[:, 2] / np.maximum(np.linalg.norm(R, axis=1), 1e-9) > 0.15)
    if spec.get('beard'):
        # ...but a beard does, below the nose's base, off the lips.
        lips = inside_hull(project(X[[mp[i] for i in LIPS if i in mp]], front['cam'], centre)[0], Pf)
        face &= (Xg[:, 1] > X[lm['subnasale'], 1] - 0.002) | lips
    still = face.copy()
    for side_ in 'lr':
        # an ear: within `ear_cm` of its line from top to lobe
        a, b = X[lm[f'ear_top_{side_}']], X[lm[f'ear_lobe_{side_}']]
        along = np.clip((Xg - a) @ (b - a) / ((b - a) @ (b - a)), 0, 1)
        still |= np.linalg.norm(Xg - a - along[:, None] * (b - a), axis=1) < spec.get('ear_cm', 2.2) / 100
    t[still] = 0
    loc = np.full(len(X), -1)
    loc[hv] = gi
    e = np.concatenate([loc[T[:, [0, 1]]], loc[T[:, [1, 2]]], loc[T[:, [2, 0]]]])
    e = np.unique(np.sort(e[e[:, 0] != e[:, 1]], 1), axis=0)
    rows, cols = np.concatenate([e[:, 0], e[:, 1]]), np.concatenate([e[:, 1], e[:, 0]])
    # The hair rises from its edge: no further out than `rise` times the way along the skin to bare skin.
    length = np.linalg.norm(Xg[e[:, 0]] - Xg[e[:, 1]], axis=1)
    edge = still | (shown < 0.5)
    limit = np.full(G, most)
    if spec.get('beard'):
        limit[beard] = spec.get('beard_cm', 1.5) / 100
    if edge.any():
        way = dijkstra(sparse.coo_matrix((np.concatenate([length, length]), (rows, cols)), shape=(G, G)).tocsr(), indices=np.nonzero(edge)[0], min_only=True)
        limit = np.minimum(limit, spec.get('rise', 1.5) * way)
    limit[still] = 0
    t = np.minimum(t, limit)
    # ...and it is smoothed over the mesh.
    A = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(G, G)).tocsr()
    deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
    for _ in range(spec.get('smooth', 2)):
        t = 0.5 * t + 0.5 * (A @ t) / deg
        t[still] = 0
    # ...and fitted to the pictures' own outlines.
    if spec.get('fit', True):
        t = fit_outlines(t, Xg, U, loc[T], views, centre, (shown >= 0.5) & ~still, low >= 0.5, limit, A, deg,
                         reads_skin(views, head['tones']) if head.get('tones') else None)
    out[hv] = t[gi]
    # A vertex off the sheet (the inside of the mouth) has no mask to stand out by: the renderer
    # leaves it where it is, and so does this.
    on = np.zeros(len(X), bool)
    for r in RECTS:
        on |= (head['uv'][:, 0] >= r['uv'][0]) & (head['uv'][:, 0] <= r['uv'][2]) & (head['uv'][:, 1] >= r['uv'][1]) & (head['uv'][:, 1] <= r['uv'][3])
    out[~on] = 0
    return out, mid


# ---------------------------------------------------------------- an open mouth

def spread(head, field):
    """A field on the kit's vertices carried to the vertices `refine` added: each takes the
    middle of its edge's two ends, as it did in every other attribute."""
    out = np.asarray(field, float)
    for ends in head.get('splits', ()):
        out = np.concatenate([out, (out[ends[:, 0]] + out[ends[:, 1]]) / 2])
    return out


def mouth_parts(head, X):
    """The triangles round the mouth of the head X, and which of them are the inner mouth (its own
    island of the body's map, behind the lips)."""
    tri, uv, mp = head['tri'], head['uv'], head['mp']
    u0, v0, u1, v1 = MOUTH_BAG_UV
    at = uv[tri[:, 0]]
    bag = (at[:, 0] > u0) & (at[:, 0] < u1) & (at[:, 1] > v0) & (at[:, 1] < v1)
    near = (np.linalg.norm(X[tri].mean(1) - X[[mp[i] for i in LIPS]].mean(0), axis=1) < MOUTH_NEAR_M) | bag
    return tri[near], bag[near]


def mouth_opening(X, head, cam, centre, pts):
    """Where a camera sees between the lips of the head X into its mouth: a mask over a window
    of the picture round the picture's own lips (points `pts`), MOUTH_ZOOM times the picture's
    size, and the window's corner in the picture."""
    T, bag = mouth_parts(head, X)
    ring = pts[list(LIPS)]
    lo = np.floor(ring.min(0)) - MOUTH_PAD_PX
    size = tuple(int(n) for n in (np.ceil(ring.max(0)) + MOUTH_PAD_PX - lo) * MOUTH_ZOOM)
    P, z = project(X, cam, centre)
    _, tb, _ = raster((P - lo) * MOUTH_ZOOM, z, T, size)
    return (tb >= 0) & bag[np.clip(tb, 0, None)], lo


def mouth_ring(pts):
    """The picture's inner lip ring, in order round the opening."""
    return pts[[LIPS_CORNERS[0], *LIPS_UPPER, LIPS_CORNERS[1], *LIPS_LOWER[::-1]]]


def mouth_shown(pts, lo, shape, zoom=MOUTH_ZOOM):
    """The picture's own opening, inside its inner lip ring, on a window like mouth_opening's."""
    from PIL import Image, ImageDraw
    im = Image.new('L', (shape[1], shape[0]), 0)
    ImageDraw.Draw(im).polygon([tuple(q) for q in (mouth_ring(pts) - lo) * zoom], fill=1)
    return np.asarray(im, bool)


def mouth_measure(X, head, cam, centre, pts):
    """How nearly the mouth of the head X is open as the picture's is: the two openings' sizes,
    how far the drawn one's edge lies from the picture's on average (the area one covers and
    the other does not, over the picture's ring's length), how much of the two the drawn one
    shares with the picture's, and how far the lips' outer ring lies from the picture's (rms),
    in millimetres of the face."""
    got, lo = mouth_opening(X, head, cam, centre, pts)
    want = mouth_shown(pts, lo, got.shape)
    mm = 1000 / cam[3]
    ring = mouth_ring(pts)
    around = np.linalg.norm(np.diff(np.vstack([ring, ring[:1]]), axis=0), axis=1).sum() * mm
    off = (pts[list(LIPS)] - project(X[[head['mp'][i] for i in LIPS]], cam, centre)[0]) * mm
    cell = (mm / MOUTH_ZOOM) ** 2
    return {'picture_mm2': round(float(want.sum() * cell), 1), 'drawn_mm2': round(float(got.sum() * cell), 1),
            'edge_off_mm': round(float((got ^ want).sum() * cell / around), 2), 'shared': round(float((got & want).sum() / max(1, (got | want).sum())), 3),
            'ring_off_mm': round(float(np.sqrt((off ** 2).sum(1).mean())), 2)}


def mouth_edges(mask):
    """The drawn opening's own edges: its columns (window pixels), and its upper and lower edge
    down each, a little smoothed. None where the mouth is shut."""
    from scipy import ndimage
    cols = np.nonzero(mask.any(0))[0]
    if len(cols) < 8 * MOUTH_ZOOM:
        return None
    top = ndimage.uniform_filter1d(np.argmax(mask, 0)[cols].astype(float), 5, mode='nearest')
    bottom = ndimage.uniform_filter1d((mask.shape[0] - np.argmax(mask[::-1], 0))[cols].astype(float), 5, mode='nearest')
    return cols, top, bottom


def mouth_edge(mask, lo, pts):
    """Where each point of the picture's inner lip ring lies on the drawn opening's own edge
    ({point: picture pixel}): as far across the drawn opening as the point is across the
    picture's, on its upper edge for the upper lip's points and its lower for the lower lip's.
    The correspondence table cannot say (it was read on a shut mouth, where the two lips'
    edges are one line)."""
    edges = mouth_edges(mask)
    if edges is None:
        sys.exit("the smiling face's mouth is shut where the record says its front picture's is open")
    cols, top, bottom = edges
    a, b = pts[LIPS_CORNERS[0], 0], pts[LIPS_CORNERS[1], 0]
    out = {}
    for ids, edge in ((LIPS_UPPER, top), (LIPS_LOWER, bottom), (LIPS_CORNERS, (top + bottom) / 2)):
        for i in ids:
            x = cols[0] + np.clip((pts[i, 0] - a) / (b - a), 0, 1) * (cols[-1] - cols[0])
            out[i] = np.array([x + 0.5, np.interp(x, cols, edge)]) / MOUTH_ZOOM + lo
    return out


def lip_rim(head, X, ring=False):
    """The lips' inner edge: the vertices on the open boundary of the head's own island that are
    one point of the body with a vertex of the inner mouth (where the lips turn in and the
    inner mouth begins). With `ring`, the edges between them as well."""
    tri, uv = head['tri'], head['uv']
    (u0, v0, u1, v1) = RECTS[0]['uv']
    T, bag = mouth_parts(head, X)
    group = weld(head['rest'])
    inner = set(group[np.unique(T[bag])].tolist())
    T = T[~bag]
    T = T[((uv[T][:, :, 0] >= u0) & (uv[T][:, :, 0] <= u1) & (uv[T][:, :, 1] >= v0) & (uv[T][:, :, 1] <= v1)).all(1)]
    edges = open_edges(T)
    rim = np.unique(np.array(edges))
    rim = np.array([i for i in rim if int(group[i]) in inner])
    if len(rim) < 12:
        sys.exit("the lips' inner edge was not found on this body")
    if ring:
        on = set(rim.tolist())
        return rim, [e for e in edges if e[0] in on and e[1] in on]
    return rim


def lip_arcs(head, X):
    """The lips' inner edge of the head X (`lip_rim`) as its two arcs, the upper lip's first:
    each the edge's vertices in order across the face, from one corner of the mouth to the
    other, both corners in both. The edge is one ring round the mouth by the skin's own edges,
    and the corners are its two ends across the face; of the two ways round, the higher is the
    upper lip's. (`lip_sides` does not say this of the edge itself: by a corner the lower lip's
    edge is nearer over the skin to the upper lip's middle than to its own.) Read on an open
    mouth; on a shut one the two arcs lie on one line."""
    rim, edges = lip_rim(head, X, ring=True)
    nxt = {int(i): [] for i in rim}
    for a, b in edges:
        nxt[a].append(b)
        nxt[b].append(a)
    if any(len(v) != 2 for v in nxt.values()):
        sys.exit("the lips' inner edge is not one ring on this body")
    start = int(rim[np.argmin(X[rim, 0])])
    order, prev = [start], None
    while True:
        a, b = nxt[order[-1]]
        step = b if a == prev else a
        prev = order[-1]
        if step == start:
            break
        order.append(step)
    if len(order) != len(rim):
        sys.exit("the lips' inner edge is not one ring on this body")
    order = np.array(order)
    far = int(np.argmax(X[order, 0]))
    one, other = order[:far + 1], np.concatenate([order[far:], order[:1]])[::-1]
    return (one, other) if X[one, 1].mean() >= X[other, 1].mean() else (other, one)


def lip_sides(head, X):
    """Which lip each vertex of the skin round the mouth is on, read on the face at rest X: +1
    the upper, -1 the lower, 0 for the inner mouth and whatever the skin does not reach. A
    vertex is on the lip whose outer edge is nearer to it over the skin (MediaPipe's outer lip
    ring, its upper and lower middles): the lips' inner edges lie on one line when the mouth is
    shut, and each turns in behind its own lip, so neither height nor the skin beside an edge
    says which is which, but from one lip's inner edge to the other lip's outer edge the skin
    goes round by a corner."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import dijkstra
    T, bag = mouth_parts(head, X)
    skin = T[~bag]
    group = weld(head['rest'])                     # by place: a seam of the map is no edge of the skin
    e = np.concatenate([skin[:, [0, 1]], skin[:, [1, 2]], skin[:, [2, 0]]])
    w = np.linalg.norm(X[e[:, 0]] - X[e[:, 1]], axis=1) + 1e-9
    n = len(X)
    g = coo_matrix((np.concatenate([w, w]), (np.concatenate([group[e[:, 0]], group[e[:, 1]]]), np.concatenate([group[e[:, 1]], group[e[:, 0]]]))), shape=(n, n)).tocsr()
    mp = head['mp']
    far = [dijkstra(g, indices=[int(group[mp[i]]) for i in ids], min_only=True) for ids in ((37, 0, 267), (84, 17, 314))]
    on = np.zeros(n, int)
    used = np.unique(skin)
    reach = np.isfinite(far[0][group[used]]) | np.isfinite(far[1][group[used]])
    used = used[reach]
    on[used] = np.where(far[0][group[used]] <= far[1][group[used]], 1, -1)
    return on


def smile_units(head):
    """The expression units a smile is fitted with (axes.json `expressions.units`, pinned CC0
    MakeHuman targets), each as it moves this head's vertices (metres)."""
    import human_variation_kit as K
    names = json.loads(F.AXES.read_text())['expressions']['units']
    delta, _, _ = K.target_deltas()
    return {pathlib.PurePosixPath(n).stem: spread(head, delta([n])) for n in names}


def fit_smile(head, v, centre, X0):
    """The smile a front picture shows (`mouth: open`), as a move of the face's vertices from
    the head X0 (the fitted face, mouth shut, with its hair stood out): the figure rests as
    fitted and moves into this.

    The picture says where the lips are: MediaPipe's outer lip ring, on the vertices the
    correspondence table names, and its inner ring, which is the opening's own edge. No table
    can name that edge's vertices (it was read on a shut mouth, where the two lips' edges are
    one line), so they are read off the face as it is drawn: at first the lips' inner edge
    itself, as far across it as each point is across the picture's, and then, each round, the
    vertices that draw the opening's edge as the front camera sees it.

    The picture says where the rest of the face is as well: the detector's other points (the
    nose's base and wings, the cheeks, the lids, the brows), each on the vertex the table names.
    A smile lifts the cheeks and the nose's wings a little and narrows the eyes from below, and
    the mouth's units move the nose's base with the lip: fitted to the lips alone they carried
    it a centimetre up and out, further than any smile does, and the picture laid on that face
    showed the underside of a nose it does not show.

    Three things move the face onto those points. First MakeHuman's expression units for the
    mouth (`smile_units`), each side of the mouth taking its own share of each (a smile is
    rarely even, and the head is turned), none past SMILE_MOST and each held back a little:
    they carry the lips back over the teeth and the corners out and up in depth as well as
    across, and the nose's points are counted beside the lips' (SMILE_NOSE each), so a unit
    that opens the mouth by lifting the nose is not taken for it. Then what the units
    leave is taken up in the picture's own plane, twice over: the whole face smoothly (a
    thin-plate spline through all its points, SMILE_FACE_SMOOTH, moving the skin within
    SMILE_FACE_M of one; skin near an eye keeps its distance from the eye's middle, so the lids
    stay on it), and then the lips exactly (a spline through their points, dying away
    SMILE_REST_M from them, the face's other points near them held where they are), so the
    drawn lips lie on the picture's. Returns the move for every vertex of the head, the kit's
    vertices it moves (those and their moves in SMILE_UNIT_M are the smile's record), each
    unit's two shares, how nearly the opening is the picture's, and how far the face's other
    points lie from the picture's before and after (`face`)."""
    from PIL import Image, ImageDraw
    from scipy import ndimage
    from scipy.interpolate import RBFInterpolator
    from scipy.optimize import lsq_linear
    from scipy.spatial import cKDTree
    mp, pts, cam = head['mp'], v['pts'], v['cam']
    s, R = cam[3], F.rot(*cam[:3])
    mm = 1000 / s
    units = smile_units(head)
    names = sorted(units)
    xmid = float(X0[[mp[i] for i in (13, 14, 0, 17)], 0].mean())
    left = smooth(-SMILE_SIDE_M, SMILE_SIDE_M, X0[:, 0] - xmid)[:, None]
    D = [units[n] * w for n in names for w in (left, 1 - left)]
    on = lip_sides(head, X0)
    lips = {1: np.nonzero(on > 0)[0], -1: np.nonzero(on < 0)[0]}
    rim = lip_rim(head, X0)
    outer = [(mp[i], pts[i]) for i in LIPS]
    ring = pts[list(LIPS)]
    middle = X0[[mp[i] for i in LIPS]].mean(0)
    near = 1 - smooth(SMILE_NEAR_M[0], SMILE_NEAR_M[1], np.linalg.norm(X0 - middle, axis=1))
    reach = SMILE_REST_M[1] * s
    # How far each pixel is from the picture's lips, for the fade of what the units leave.
    lo = np.floor(ring.min(0) - reach - 4)
    W, H = (int(n) for n in np.ceil(ring.max(0) + reach + 4) - lo)
    im = Image.new('L', (W, H), 0)
    ImageDraw.Draw(im).polygon([tuple(q) for q in ring - lo], fill=1)
    far = ndimage.distance_transform_edt(np.asarray(im) == 0).astype(np.float32) / s
    c2 = ring.mean(0)
    out2 = ring - c2
    anchors = ring + out2 / np.linalg.norm(out2, axis=1, keepdims=True) * reach
    proj = lambda X: project(X, cam, centre)[0]
    # The rest of the face: the detector's points off the lips, each on its own vertex (those it
    # spreads over the lips between its two rings were read on a shut mouth, some on the other lip).
    im = Image.new('L', v['size'], 0)
    ImageDraw.Draw(im).polygon([tuple(q) for q in ring], fill=1)
    on_lips = np.asarray(im, bool)
    off_lips = lambda i: not on_lips[int(np.clip(pts[i, 1], 0, v['size'][1] - 1)), int(np.clip(pts[i, 0], 0, v['size'][0] - 1))]
    face = [i for i in sorted(mp) if i not in LIPS and off_lips(i)]
    face_rows, face_at = np.array([mp[i] for i in face]), pts[face]
    marked = np.unique(np.concatenate([face_rows, [mp[i] for i in LIPS], rim]))
    hv = np.unique(head['tri'][X0[head['tri']][:, :, 1].mean(1) > X0[:, 1].max() - HEAD_DROP_M])
    with_face = np.zeros(len(X0))
    with_face[hv] = 1 - smooth(SMILE_FACE_M[0], SMILE_FACE_M[1], cKDTree(X0[marked]).query(X0[hv])[0])
    eyes = list(bones_rest(head['asset'], ('eye_l', 'eye_r')).values())
    face_off = lambda X: float(np.sqrt((((proj(X)[face_rows] - face_at) * mm) ** 2).sum(1).mean()))
    lm = head['lm']
    at_nose = (np.abs(X0[face_rows, 0] - xmid) < SMILE_NOSE_M[0]) & (X0[face_rows, 1] > X0[lm['subnasale'], 1] - SMILE_NOSE_M[1]) & (X0[face_rows, 1] < X0[lm['nasion'], 1])
    nose_rows, nose_at = face_rows[at_nose], face_at[at_nose]

    def inner(X):
        """The picture's inner ring, each point with the vertex that should lie on it: on a
        shut mouth the lips' inner edge itself, on an open one the vertex nearest the drawn
        opening's edge there, of that lip."""
        P = proj(X)
        mask, wlo = mouth_opening(X, head, cam, centre, pts)
        if mouth_edges(mask) is None:
            a, b = pts[LIPS_CORNERS[0], 0], pts[LIPS_CORNERS[1], 0]
            cons = []
            for ids, side in ((LIPS_UPPER, 1), (LIPS_LOWER, -1)):
                r = rim[on[rim] == side]
                r = r[np.argsort(P[r, 0])]
                cons += [(int(r[int(round(np.clip((pts[i, 0] - a) / (b - a), 0, 1) * (len(r) - 1)))]), pts[i]) for i in ids]
            r = rim[np.argsort(P[rim, 0])]
            return cons + [(int(r[0]), pts[LIPS_CORNERS[0]]), (int(r[-1]), pts[LIPS_CORNERS[1]])]
        cons = []
        for i, at in mouth_edge(mask, wlo, pts).items():
            among = lips[1] if i in LIPS_UPPER else lips[-1] if i in LIPS_LOWER else rim
            cons.append((int(among[np.argmin(((P[among] - at) ** 2).sum(1))]), pts[i]))
        return cons

    def by_units(cons):
        # one target a vertex: where several of the picture's points fall to one, their middle
        rows = sorted({j for j, _ in cons})
        want = np.array([np.mean([q for j, q in cons if j == r], axis=0) for r in rows])
        rows = np.array(rows)
        A = np.stack([((d[rows] @ R.T)[:, :2] * np.array([s, -s]) * mm).ravel() for d in D], 1)
        miss = ((want - proj(X0)[rows]) * mm).ravel()
        # ...and the nose beside them: what a unit does to its base and wings counts
        Af = np.stack([((d[nose_rows] @ R.T)[:, :2] * np.array([s, -s]) * mm).ravel() for d in D], 1) * SMILE_NOSE
        mf = ((nose_at - proj(X0)[nose_rows]) * mm).ravel() * SMILE_NOSE
        ridge = SMILE_RIDGE_MM * np.sqrt(len(rows)) * np.eye(len(D))
        w = lsq_linear(np.vstack([A, Af, ridge]), np.concatenate([miss, mf, np.zeros(len(D))]), bounds=(0, SMILE_MOST)).x
        return w, X0 + sum(wk * d for wk, d in zip(w, D))

    def lips_drawn(X, P):
        """Where the lips are drawn and where the picture has them: the outer ring from its
        vertices, the inner from the opening's edge (whichever part of a lip draws it)."""
        at = [P[mp[i]] for i in LIPS]
        to = [pts[i] for i in LIPS]
        mask, wlo = mouth_opening(X, head, cam, centre, pts)
        if mouth_edges(mask) is not None:
            for i, e in mouth_edge(mask, wlo, pts).items():
                at.append(e)
                to.append(pts[i])
        return np.array(at), np.array(to)

    def whole_face(X):
        """The whole face onto its points in the picture, smoothly and in the picture's plane:
        the cheeks, the nose's wings and the lids as well as the lips. Skin near an eye is then
        set back or forward along the camera's line to the distance it stood from the eye's
        middle, so a lid that rises stays on the eye."""
        P = proj(X)
        at, to = lips_drawn(X, P)
        at, to = np.vstack([at, P[face_rows]]), np.vstack([to, face_at])
        follow = RBFInterpolator(at, to - at, kernel='thin_plate_spline', smoothing=SMILE_FACE_SMOOTH)
        k = np.nonzero(with_face > 0)[0]
        d = follow(P[k]) * with_face[k, None] / s
        was = X[k]
        X = X.copy()
        X[k] += np.stack([d[:, 0], -d[:, 1], np.zeros(len(k))], 1) @ R
        for c in eyes:
            r0 = np.linalg.norm(was - c, axis=1)
            j = np.nonzero(r0 < SMILE_EYE_M[1])[0]
            q = X[k[j]] - c
            b = q @ R[2]
            disc = b * b - ((q * q).sum(1) - r0[j] ** 2)
            ok = disc >= 0
            t = np.where(b >= 0, -b + np.sqrt(np.maximum(disc, 0)), -b - np.sqrt(np.maximum(disc, 0)))
            X[k[j[ok]]] += ((1 - smooth(SMILE_EYE_M[0], SMILE_EYE_M[1], r0[j[ok]])) * t[ok])[:, None] * R[2]
        return X

    def in_plane(X):
        """What is left, taken up in the picture's plane: the lips' outer ring from where its
        vertices are drawn, the inner ring from where the opening's edge is drawn (whichever
        part of a lip draws it), smoothly between, and nothing SMILE_REST_M from the lips."""
        P = proj(X)
        at, to = lips_drawn(X, P)
        # the face's other points within reach of the lips hold where the whole face's move left them
        q = P[face_rows] - lo
        hold = P[face_rows][(q[:, 0] > 1) & (q[:, 0] < W - 2) & (q[:, 1] > 1) & (q[:, 1] < H - 2)]
        left_over = RBFInterpolator(np.vstack([at, hold, anchors]), np.vstack([to - at, np.zeros_like(hold), np.zeros_like(anchors)]), kernel='thin_plate_spline', smoothing=1.0)
        q = P - lo
        k = np.nonzero((near > 0) & (q[:, 0] > 1) & (q[:, 0] < W - 2) & (q[:, 1] > 1) & (q[:, 1] < H - 2))[0]
        fade = near[k] * (1 - smooth(SMILE_REST_M[0], SMILE_REST_M[1], sample(far[:, :, None], q[k])[:, 0]))
        k, fade = k[fade > 0], fade[fade > 0]
        d = left_over(P[k]) * fade[:, None] / s
        X = X.copy()
        X[k] += np.stack([d[:, 0], -d[:, 1], np.zeros(len(k))], 1) @ R
        return X

    # The units first, twice: on the lips' inner edge, then on the vertices that draw the opening.
    w, X = by_units(outer + inner(X0))
    w, X = by_units(outer + inner(X))
    best = None
    for _ in range(SMILE_ROUNDS):
        X = in_plane(whole_face(X))
        m = mouth_measure(X, head, cam, centre, pts)
        if best is None or m['edge_off_mm'] ** 2 + 0.25 * m['ring_off_mm'] ** 2 < best[0]:
            best = (m['edge_off_mm'] ** 2 + 0.25 * m['ring_off_mm'] ** 2, X)
    X = best[1]
    # As the record keeps it and the renderer draws it: the kit's vertices, in the kit's unit.
    n = head['kit_n']
    d = X[:n] - X0[:n]
    moved = np.nonzero(np.linalg.norm(d, axis=1) >= SMILE_DROP_M)[0]
    q = np.round(d[moved] / SMILE_UNIT_M).astype(int)
    if np.abs(q).max(initial=0) >= 32767:
        sys.exit('a smile moves a vertex further than its record can hold')
    kept = np.zeros((n, 3))
    kept[moved] = q * SMILE_UNIT_M
    delta = spread(head, kept)
    return {'delta': delta, 'vertices': moved, 'moves': q,
            'units': {name: [round(float(w[2 * k]), 3), round(float(w[2 * k + 1]), 3)] for k, name in enumerate(names)},
            'most_m': round(float(np.linalg.norm(kept, axis=1).max(initial=0)), 5),
            'measured': mouth_measure(X0 + delta, head, cam, centre, pts),
            'face': {'points': len(face), 'rest_off_mm': round(face_off(X0), 2), 'off_mm': round(face_off(X0 + delta), 2)}}


def teeth_strip(X, head, v, centre):
    """The teeth of an open mouth, as the front picture shows them: a strip of TEETH['grid']
    points behind the lips of the smiling head X. Across, it follows the lips' inner edge from
    corner to corner (a parabola through `lip_rim`, back from the middle to the corners), set
    behind every point of that edge by TEETH['back_m'] at the least; it stands TEETH['over_m']
    above the upper lip's edge, below the lower lip's and past the corners, hidden there in
    the lips, so a mouth that shuts or a jaw that drops never shows its end. Its colour is the
    front picture's: each point, as the front camera sees it in the drawn opening, takes the
    picture's pixel as far across the picture's opening and as far down between its lips.
    Returns the points (metres, the body's rest frame), their pixels in the front picture,
    and the share of the drawn opening in which the
    camera sees the strip and not the inner mouth behind it."""
    cam, pts = v['cam'], v['pts']
    rim = lip_rim(head, X)
    xm = float(X[rim, 0].mean())
    (a, b), *_ = np.linalg.lstsq(np.stack([np.ones(len(rim)), (X[rim, 0] - xm) ** 2], 1), X[rim, 2], rcond=None)
    b = min(float(b), 0.0)
    behind = max(0.0, float((a + b * (X[rim, 0] - xm) ** 2 - X[rim, 2]).max()))
    nc, nr = TEETH['grid']
    up, down, past = TEETH['over_m']
    xs = np.linspace(X[rim, 0].min() - past, X[rim, 0].max() + past, nc)

    def edge(arc):
        r = arc[np.argsort(X[arc, 0])]
        return np.interp(xs, X[r, 0], X[r, 1])

    yu, yl = (edge(arc) for arc in lip_arcs(head, X))
    ym = (yu + yl) / 2
    top, bottom = np.maximum(yu, ym + 0.001) + up, np.minimum(yl, ym - 0.001) - down
    zs = a - TEETH['back_m'] - behind + b * (xs - xm) ** 2
    at = np.stack([np.repeat(xs[None], nr, 0), top[None] + (bottom - top)[None] * np.linspace(0, 1, nr)[:, None], np.repeat(zs[None], nr, 0)], -1).reshape(-1, 3)
    # The picture's pixel for each point: opening to opening.
    mask, lo = v['opening']
    cols, etop, ebottom = mouth_edges(mask)
    cx, ty, by = (cols + 0.5) / MOUTH_ZOOM + lo[0], etop / MOUTH_ZOOM + lo[1], ebottom / MOUTH_ZOOM + lo[1]
    pa, pb = pts[LIPS_CORNERS[0]], pts[LIPS_CORNERS[1]]
    upper, lower = pts[[LIPS_CORNERS[0], *LIPS_UPPER, LIPS_CORNERS[1]]], pts[[LIPS_CORNERS[0], *LIPS_LOWER, LIPS_CORNERS[1]]]
    upper, lower = upper[np.argsort(upper[:, 0])], lower[np.argsort(lower[:, 0])]
    P = project(at, cam, centre)[0]
    px = pa[0] + (P[:, 0] - cx[0]) / (cx[-1] - cx[0]) * (pb[0] - pa[0])
    t0, b0 = np.interp(P[:, 0], cx, ty), np.interp(P[:, 0], cx, by)
    t1, b1 = np.interp(px, upper[:, 0], upper[:, 1]), np.interp(px, lower[:, 0], lower[:, 1])
    share = (P[:, 1] - t0) / np.maximum(b0 - t0, 1.0)
    py = np.where(P[:, 1] < t0, t1 - (t0 - P[:, 1]), np.where(P[:, 1] > b0, b1 + (P[:, 1] - b0), t1 + share * (b1 - t1)))
    # What the front camera sees in the opening: the strip, or the inner mouth in front of it.
    T, bag = mouth_parts(head, X)
    grid = np.arange(nc * nr).reshape(nr, nc) + len(X)
    cells = np.stack([grid[:-1, :-1], grid[1:, :-1], grid[:-1, 1:], grid[:-1, 1:], grid[1:, :-1], grid[1:, 1:]], -1).reshape(-1, 3)
    Pa, za = project(np.vstack([X, at]), cam, centre)
    _, tb, _ = raster((Pa - lo) * MOUTH_ZOOM, za, np.vstack([T, cells]), mask.shape[::-1])
    strip, inner = tb >= len(T), (tb >= 0) & (tb < len(T)) & bag[np.clip(tb, 0, len(T) - 1)]
    return {'at': at, 'px': np.stack([px, py], 1), 'rim': len(rim), 'behind_m': round(behind, 5),
            'shown': round(float(strip.sum() / max(1, (strip | inner).sum())), 3)}


def teeth_patch(strip, v):
    """The front picture's pixels the strip takes, as a patch for the sheet, and each of the
    strip's points on it (sheet pixels). The picture's own opening is kept; round it, where the
    strip stands hidden in the lips, the teeth's colours are carried outward (the lips' are
    not: a jaw that drops shows a little more of the strip, never a lip painted on teeth). The
    patch is turned a quarter (the mouth's width down the sheet) to fit TEETH['px']."""
    from PIL import Image
    from scipy import ndimage
    x0, y0, x1, y1 = TEETH['px']
    lo = np.floor(strip['px'].min(0)).astype(int) - TEETH['pad_px']
    hi = np.ceil(strip['px'].max(0)).astype(int) + TEETH['pad_px']
    W, H = v['size']
    if lo.min() < 0 or hi[0] > W or hi[1] > H:
        sys.exit("the front picture's mouth lies off its quadrant")
    crop = v['img'][lo[1]:hi[1], lo[0]:hi[0]].copy()
    inside = ndimage.binary_erosion(mouth_shown(v['pts'], lo.astype(float), crop.shape[:2], 1), iterations=1)
    crop = diffuse_fill(crop, ~inside, known=inside)
    w, h = hi - lo
    scale = min(1.0, (x1 - x0) / h, (y1 - y0) / w)
    if scale < 1:
        crop = np.asarray(Image.fromarray((np.clip(crop, 0, 1) * 255).astype(np.uint8)).resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)).astype(np.float32) / 255
    turned = np.rot90(crop)                       # the picture's right edge at the top
    th, tw = turned.shape[:2]
    box = np.pad(turned, ((0, (y1 - y0) - th), (0, (x1 - x0) - tw), (0, 0)), mode='edge')
    q = (strip['px'] - lo) * scale
    return box, np.stack([x0 + q[:, 1], y0 + (crop.shape[1] - q[:, 0])], 1)


def front_layer(v, X, head, T, centre, share):
    """The front picture as the renderer shows it to someone standing in front of the face.

    The sheet gives each texel one colour, and hair that stands beside a face is seen from the
    front and from the side: the two pictures show two different things there (the locks'
    fronts; the hair swept back over the ear), and whichever the sheet takes is wrong from the
    other side. So the front picture is kept as well, as a picture: the square of it round the
    head, its ground and clothing filled from the head beside them, and beside it where it is
    to be shown (`share`: the front picture's own share of each texel of the sheet, none of
    one that was filled, drawn as the front camera sees the grown head at rest; the picture
    is shown where that is low, outside the face's own outline drawn in a little). The
    renderer lays it on the skin by
    where each point stands (`u`, `v`: the picture's across and down, 0..1, from a place in
    the body's rest frame, metres), for an eye near the line the picture was taken along
    (`toward`), and the sheet's own colour from anywhere else."""
    from PIL import Image, ImageDraw
    from scipy import ndimage
    W, H = v['size']
    n, na, pad = FRONT['px'], FRONT['alpha_px'], FRONT['pad_px']
    ys, xs = np.nonzero(v['head'])
    side = float(max(xs.max() - xs.min(), ys.max() - ys.min()) + 1 + 2 * pad)
    bx, by = (xs.min() + xs.max() + 1 - side) / 2, (ys.min() + ys.max() + 1 - side) / 2
    # Where the sheet is the front picture already, as the front camera sees the head at rest.
    P, z = project(X, v['cam'], centre)
    _, tb, bary = raster(P, z, T, (W, H))
    m = tb >= 0
    t, b = T[tb[m]], bary[m].astype(np.float64)
    uvp = (head['uv'][t] * b[:, :, None]).sum(1)
    (u0, v0, u1, v1), (x0, y0, x1, y1) = RECTS[0]['uv'], RECTS[0]['px']
    inside = (uvp[:, 0] >= u0) & (uvp[:, 0] <= u1) & (uvp[:, 1] >= v0) & (uvp[:, 1] <= v1)
    at = np.stack([x0 + (uvp[:, 0] - u0) / (u1 - u0) * (x1 - x0), y0 + (uvp[:, 1] - v0) / (v1 - v0) * (y1 - y0)], 1)
    other = np.zeros((H, W), np.float32)
    other[m] = np.where(inside, 1 - sample(share[:, :, None], at)[:, 0], 0.0)
    # ...carried out past the drawn head's own outline (the renderer's stands a little apart).
    near = ndimage.distance_transform_edt(~m, return_distances=False, return_indices=True)
    other = other[near[0], near[1]]
    oval = Image.new('L', (W, H), 0)
    ImageDraw.Draw(oval).polygon([tuple(q) for q in v['pts'][list(FRONT_OVAL)]], fill=1)
    face = ndimage.binary_erosion(np.asarray(oval, bool), iterations=FRONT['face_in_px'])
    alpha = ndimage.gaussian_filter(other * ~face, FRONT['soft_px'])
    # ...and what the picture shows at each place, hair or skin: the renderer lays it on by
    # where a place stands, not by what the camera saw, so hair that stands behind an ear took
    # the ear's skin (pale scraps in the hair, to someone a little to one side). It shows the
    # picture's hair on hair and its skin on skin.
    kind = np.zeros((H, W), np.float32)
    kind[m] = (head['hair'][t] * b).sum(1)
    kind = kind[near[0], near[1]]
    # ...the picture's own pixels, less its white ground: round the head, in the outline's own
    # blur (as far in as the sheet leaves it out), and through the hair. Past the outline the
    # picture goes on as the hair inside it does, mirrored in the outline: the renderer's head
    # stands a little outside the picture's in places, and filled pale from the outline's blur
    # it showed pale scraps in the hair there to someone a little to one side.
    keep = ndimage.binary_erosion(v['head'], iterations=FRONT['outline_in_px']) & ~(v['ground'] > 0.5)
    # ...and next to the outline nothing pale: the ground between wisps of hair, an earring's glint.
    keep &= ndimage.binary_erosion(v['head'], iterations=FRONT['rim_px']) | (v['img'].min(2) < FRONT['rim_pale'])
    colour = mirror_fill(v['img'], ~keep, keep, reach=FRONT['mirror_px'])
    gx, gy = np.meshgrid(bx + (np.arange(n) + 0.5) * side / n, by + (np.arange(n) + 0.5) * side / n)
    grid = np.stack([gx.ravel(), gy.ravel()], 1)
    out = np.zeros((n, n + na, 3), np.float32)
    out[:, :n] = sample(colour, grid).reshape(n, n, 3)
    a = sample(alpha[:, :, None], grid).reshape(n, n)
    block = lambda q: q.reshape(na, n // na, na, n // na).mean((1, 3))[:, :, None]
    out[:na, n:] = block(a)
    out[na:2 * na, n:] = block(sample(kind[:, :, None], grid).reshape(n, n))
    R, s = F.rot(*v['cam'][:3]), v['cam'][3]
    return {'image': out,
            'u': [float(c) for c in s * R[0] / side] + [float((v['cam'][4] - bx - s * R[0] @ centre) / side)],
            'v': [float(c) for c in -s * R[1] / side] + [float((v['cam'][5] - by + s * R[1] @ centre) / side)],
            'toward': [float(c) for c in R[2]], 'shown': float(a.mean())}


def bake(rec, sheet, head, smile_at=None):
    from PIL import Image, ImageDraw
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
    X = X0 + away(X0, mid) * thick[:, None]
    group = weld(head['rest'])

    def normals(Xs):
        n = np.zeros_like(Xs)
        np.add.at(n, group, vertex_normals(Xs, head['tri']))
        return (n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12))[group]

    N = normals(X)
    # A front picture whose mouth is open shows a smile: the face is fitted into it (the figure
    # rests as fitted, mouth shut, and moves into the smile), and that picture is laid on the
    # smiling face; the others, on the face at rest they were taken of.
    # ...or the sheet shows the mouth shut and the record names a picture of the smile by itself
    # (`smile_view`): the face is fitted into that one, which is laid on nothing.
    grin = views[0] if views[0].get('mouth') == 'open' else read_smile_view(rec, smile_at, head, centre)
    smile = fit_smile(head, grin, centre, X) if grin is not None else None
    idx = sorted(mp)
    hv = np.unique(T)
    for v in views:
        smiling = smile is not None and v is grin
        Xv = X + smile['delta'] if smiling else X
        P, z = project(Xv, v['cam'], centre)
        zb, _, _ = raster(P, z, T, v['size'])
        Pw = P.copy()
        if v['name'] == 'front':
            # The picture's own features onto the mesh's: a thin-plate spline through the points.
            use = list(idx)
            if smiling:
                # ...its inner lip ring onto the edge of the opening the drawn lips leave, and
                # the points the detector spreads over the lips between its two rings left out
                # (the table read them on a shut mouth, some on the other lip).
                v['opening'] = mouth_opening(Xv, head, v['cam'], centre, v['pts'])
                edge = mouth_edge(*v['opening'], v['pts'])
                im = Image.new('L', v['size'], 0)
                ImageDraw.Draw(im).polygon([tuple(q) for q in v['pts'][list(LIPS)]], fill=1)
                on_lips = np.asarray(im, bool)
                W_, H_ = v['size']
                between = lambda i: on_lips[int(np.clip(v['pts'][i, 1], 0, H_ - 1)), int(np.clip(v['pts'][i, 0], 0, W_ - 1))]
                use = [i for i in idx if i in edge or i in LIPS or not between(i)]
                # The picture's own opening: its pixels are the teeth's, never the lips'.
                v['open_px'] = ndimage.binary_dilation(mouth_shown(v['pts'], np.zeros(2), (H_, W_), 1), iterations=1).astype(np.float32)
            src, dst = P[[mp[i] for i in use]], v['pts'][use]
            if smiling:
                for i, at in edge.items():
                    src[use.index(i)] = at
            v['warp'] = RBFInterpolator(src, dst - src, kernel='thin_plate_spline', smoothing=2.0)
            Pw[hv] = P[hv] + v['warp'](P[hv])
        low = v['img'].min(2)
        ground = ndimage.binary_dilation((low > HAIR_GROUND[0]) & (v['img'].max(2) - low < HAIR_GROUND[1]), iterations=2)
        v.update(P=P, Pw=Pw, z=z, zb=ndimage.maximum_filter(zb, 3), nz=((normals(Xv) if smiling else N) @ F.rot(*v['cam'][:3]).T)[:, 2], ground=ground.astype(np.float32))
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
    ears_z = max(X0[lm[k], 2] for k in ('ear_top_l', 'ear_top_r', 'ear_lobe_l', 'ear_lobe_r'))
    tops_y = min(X0[lm['ear_top_l'], 1], X0[lm['ear_top_r'], 1])
    lobes_y = max(X0[lm['ear_lobe_l'], 1], X0[lm['ear_lobe_r'], 1])
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
        raw, square, cols, graze = [], [], [], []
        for v in views:
            W, H = v['size']
            p = (v['P'][t] * b[:, :, None]).sum(1)
            pw = (v['Pw'][t] * b[:, :, None]).sum(1)
            zz, nz = (v['z'][t] * b).sum(1), (v['nz'][t] * b).sum(1)
            xi, yi = np.clip(p[:, 0].astype(int), 0, W - 1), np.clip(p[:, 1].astype(int), 0, H - 1)
            w = (zz > v['zb'][yi, xi] - 0.012) * ((pw[:, 0] > 1) & (pw[:, 0] < W - 1) & (pw[:, 1] > 1) & (pw[:, 1] < H - 1))
            w = w * smooth(0.6, 1.0, sample(v['good'][:, :, None], pw)[:, 0])
            # ...and where the hair stands out, not the sheet's white ground seen through it
            w = w * (1 - smooth(0.002, 0.004, th) * smooth(0.1, 0.4, sample(v['ground'][:, :, None], pw)[:, 0]))
            graze.append(w * smooth(GRAZE[0], GRAZE[1], nz) * (1 - sample(v['open_px'][:, :, None], pw)[:, 0] if 'open_px' in v else 1.0))
            if v['name'] == 'front':
                w = w * smooth(0.12, 0.45, nz)
                if 'open_px' in v:
                    w = w * (1 - sample(v['open_px'][:, :, None], pw)[:, 0])
            elif v['name'] == 'back':
                w = w * smooth(0.10, 0.5, nz)
            else:
                w = w * smooth(0.08, 0.4, nz) * smooth(-0.005, 0.02, (1.0 if v['name'] == 'left' else -1.0) * (pos[:, 0] - xmid))
            raw.append(w)
            square.append(np.clip(nz, 0, 1))
            cols.append(sample(v['img'], pw))
        raw, square = np.stack(raw, 1), np.stack(square, 1)
        # Hair beside the face, in front of the ears and above their lobes (a temple's), is the
        # side pictures' wherever one sees it: the front picture looks along it, into its shadow,
        # and laid on the hair's own front it stood as a dark strip down the temple from the side.
        temple = (smooth(ears_z - 0.01, ears_z + 0.005, pos[:, 2]) * smooth(0.035, 0.05, lat) * smooth(0.001, 0.004, th)
                  * smooth(tops_y - 0.035, tops_y - 0.015, pos[:, 1]))
        raw[:, 0] *= 1 - HAIR_TEMPLE * temple * smooth(0.05, 0.25, raw[:, 1:3].max(1))
        # ...and what the front picture shows of it as shade (it looks past the locks, into the
        # hair's own shadow: laid on the hair, a black notch at the hairline from the side) is
        # no picture's, and the hair there takes the hair's beside it.
        # The same of the skin under the hairline there, above the brows: the hair's shadow on
        # it, which the side picture shows lit.
        corner = (smooth(ears_z - 0.01, ears_z + 0.005, pos[:, 2]) * smooth(0.035, 0.05, lat)
                  * smooth(tops_y + 0.010, tops_y + 0.025, pos[:, 1]))
        shade = np.maximum(temple, corner) * (1 - smooth(TEMPLE_SHADE[0], TEMPLE_SHADE[1], cols[0].max(1)))
        raw[:, 0] *= 1 - shade
        graze[0] = graze[0] * (1 - shade)
        # Within the face's own width the front goes first, and what it leaves goes to whichever
        # other view sees the texel best...
        wf = raw[:, 0]
        others = raw[:, 1:]
        share = others ** 2
        share = share / np.maximum(share.sum(1, keepdims=True), 1e-9) * np.clip(others.max(1, keepdims=True) * 3, 0, 1)
        first = np.concatenate([wf[:, None], (1 - wf)[:, None] * share], 1)
        # ...and past it the hair that stands out goes to whichever view sees it most squarely
        # (the curls that hang below the ears face the front picture, and are its), the front
        # picture counting for less from the ears' lobes up (it looks along the hair swept back
        # over an ear, and what it shows there, laid on hair a side picture also sees, stood as
        # scraps of another colour round the ear), and the skin, an ear above all, to its own
        # side's picture before any other.
        less = np.ones((len(pos), 4))
        less[:, 0] = 1 - HAIR_FRONT_LESS * smooth(lobes_y - 0.01, lobes_y + 0.005, pos[:, 1])
        each = (raw * square ** 2 * less) ** 2
        side = (raw * np.array([0.2, 1.0, 1.0, 0.2])) ** 2
        stands = smooth(0.002, 0.006, th)[:, None]
        each = each / np.maximum(each.sum(1, keepdims=True), 1e-9) * stands + side / np.maximum(side.sum(1, keepdims=True), 1e-9) * (1 - stands)
        each = each * np.clip(raw.max(1, keepdims=True) * 3, 0, 1)
        wide = smooth(0.050, 0.066, lat)[:, None]
        ws = first * (1 - wide) + each * wide
        # What no picture sees squarely (the underside of a beard, which the front picture looks
        # along) takes the picture that sees it at all, the one it most nearly faces, for as
        # much as the others leave: its own colour there, drawn out, before its neighbours'.
        graze = np.stack(graze, 1)
        most = graze.argmax(1)
        ws[np.arange(len(ws)), most] += graze.max(1) * (1 - smooth(0.0, 0.35, ws.sum(1)))
        tot = ws.sum(1)
        tex[y0:y1, x0:x1][m] = sum(cols[k] * ws[:, k:k + 1] for k in range(len(views))) / np.maximum(tot, 1e-6)[:, None]
        seen[y0:y1, x0:x1][m] = np.clip(tot, 0, 1)
        cover[y0:y1, x0:x1][m] = True
        front[y0:y1, x0:x1][m] = ws[:, 0]
        lateral[y0:y1, x0:x1][m] = lat
        height[y0:y1, x0:x1][m] = pos[:, 1]
        stand[y0:y1, x0:x1][m] = th
        hairy[y0:y1, x0:x1][m] = (head['hair'][t] * b).sum(1)
        facing[y0:y1, x0:x1][m] = (N[t] * b[:, :, None]).sum(1)
        # The head above the chin is whole; of the neck, only what a picture shows. Hair that
        # stands out is whole wherever it stands (no picture looks up at a beard from under
        # the chin, and the skin it grows from was left the body's own, pushed out).
        whole = smooth(chin + NECK_KEEP_M[0], chin + NECK_KEEP_M[1], pos[:, 1]) if r['name'] != 'neck' else 0.0
        alpha[y0:y1, x0:x1][m] = np.maximum(np.maximum(np.clip(tot, 0, 1), whole), smooth(HAIR_WHOLE_M[0], HAIR_WHOLE_M[1], th))
    # Where the hair stands out, as cells of the sheet: the renderer splits the skin's triangles there.
    cw, ch = TW // FINE_CELL_PX, TH // FINE_CELL_PX
    cells = ((stand > FINE_STAND_M) & cover).reshape(ch, FINE_CELL_PX, cw, FINE_CELL_PX).any((1, 3))
    cells = ndimage.binary_dilation(cells, structure=np.ones((3, 3), bool))
    # What no picture shows takes its neighbours' colour: hair from hair first (behind an ear the
    # skin beside it is the ear's), then the rest. That is every such texel, the ones the mask
    # leaves out too: the mask is feathered, and left black they darkened its edge (a dark
    # band along the underside of a beard).
    hole = cover & (seen < 0.35)
    hairs = cover & (stand > FINE_STAND_M)
    # ...and hair that took the sheet's white ground (seen between the curls at an outline) is
    # filled as what no picture shows is: laid on the hair it stood as white scraps on the crown.
    low = tex.min(2)
    hole |= hairs & ndimage.binary_dilation(hairs & (low > HAIR_GROUND[0]) & (tex.max(2) - low < HAIR_GROUND[1]))
    filled = hole.copy()
    if (hole & hairs).any() and (hairs & ~hole).any():
        tex = mirror_fill(tex, hole & hairs, hairs & ~hole)
        hole &= ~hairs
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
    # A smile's teeth: the strip behind the lips, and its patch of the front picture.
    teeth = None
    if smile is not None:
        mouth = smile['measured']
        if mouth['edge_off_mm'] > MOUTH_HOLDS[0] or mouth['ring_off_mm'] > MOUTH_HOLDS[1]:
            sys.exit(f"{rec['person_id']}: the smile fitted to its picture does not open as the picture's mouth does ({mouth})")
        if smile['face']['off_mm'] > min(SMILE_FACE_HOLDS_MM, smile['face']['rest_off_mm']):
            sys.exit(f"{rec['person_id']}: the smile fitted to its picture leaves the rest of the face off the picture's ({smile['face']})")
        if grin is not views[0]:
            # A picture of its own was not laid on the skin: its opening is read here, and its
            # teeth are brought into the sheet's light.
            grin['opening'] = mouth_opening(X + smile['delta'], head, grin['cam'], centre, grin['pts'])
            smile['tone'] = [round(float(c), 3) for c in smile_tone(grin, views[0])]
            grin['img'] = linear_to_srgb(np.clip(srgb_to_linear(grin['img']) * np.array(smile['tone'], np.float32), 0, 1))
            smile['camera'] = {'yaw_deg': round(float(np.degrees(grin['cam'][0])), 1), 'pitch_deg': round(float(np.degrees(grin['cam'][1])), 1),
                               'roll_deg': round(float(np.degrees(grin['cam'][2])), 1), 'px_per_m': round(float(grin['cam'][3]), 1), 'miss_mm': round(grin['miss_mm'], 2)}
            smile['laid_on'] = grin['laid_on']
        strip = teeth_strip(X + smile['delta'], head, grin, centre)
        if strip['shown'] < TEETH['shown']:
            sys.exit(f"{rec['person_id']}: the smile's camera sees the inner mouth, not the teeth, in too much of the opening ({strip['shown']})")
        x0, y0, x1, y1 = TEETH['px']
        if ndimage.binary_dilation(cover, iterations=4)[y0:y1, x0:x1].any():
            sys.exit(f"{rec['person_id']}: the teeth's corner of the sheet is not free on this body")
        tex[y0:y1, x0:x1], at_px = teeth_patch(strip, grin)
        soft[y0:y1, x0:x1], stand[y0:y1, x0:x1], hairy[y0:y1, x0:x1] = 1.0, 0.0, 0.0
        (u0, v0, u1, v1), (rx0, ry0, rx1, ry1) = RECTS[0]['uv'], RECTS[0]['px']
        teeth = {'at': strip['at'], 'uv': np.stack([u0 + (at_px[:, 0] - rx0) / (rx1 - rx0) * (u1 - u0), v0 + (at_px[:, 1] - ry0) / (ry1 - ry0) * (v1 - v0)], 1),
                 'shown': strip['shown'], 'behind_m': strip['behind_m']}
        head['smiling'] = X + smile['delta']
        head['teeth'] = teeth
    head['grown'] = X
    # The front picture itself, for the renderer to show from the front where the sheet took another picture.
    # (A texel that was filled holds no picture's colour: the front picture has no share of it.)
    layer = front_layer(views[0], X, head, T, centre, np.where(filled, 0.0, front / np.maximum(seen, 1e-3)))
    cams = {v['name']: {'yaw_deg': round(float(np.degrees(v['cam'][0])), 1), 'pitch_deg': round(float(np.degrees(v['cam'][1])), 1),
                        'roll_deg': round(float(np.degrees(v['cam'][2])), 1), 'px_per_m': round(float(v['cam'][3]), 1),
                        **({'miss_mm': round(v['miss_mm'], 2)} if 'miss_mm' in v else {}),
                        **({'lined_up': v['lined_up']} if 'lined_up' in v else {}), **v['left_out']} for v in views}
    return tex, soft, tone, cams, {'stand': stand, 'hair': hairy, 'facing': facing, 'mid': mid, 'max_m': float(thick.max()), 'read': read, 'lids': lids, 'eyes': eyes, 'cells': cells,
                                 'teeth': teeth, 'smile': smile, 'front': layer}


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
    """A strip of turns of the bare head under the baked skin, to look at (not the renderer);
    for a face that smiles, a second strip of it smiling, its teeth behind the lips."""
    from PIL import Image
    rows = [_preview_row(head, head.get('grown', head['X']), head['tri'], head['uv'], tex, soft, turns, size)]
    if 'smiling' in head:
        nc, nr = TEETH['grid']
        grid = np.arange(nc * nr).reshape(nr, nc) + len(head['smiling'])
        cells = np.stack([grid[:-1, :-1], grid[1:, :-1], grid[:-1, 1:], grid[:-1, 1:], grid[1:, :-1], grid[1:, 1:]], -1).reshape(-1, 3)
        rows.append(_preview_row(head, np.vstack([head['smiling'], head['teeth']['at']]), np.vstack([head['tri'], cells]),
                                 np.vstack([head['uv'], head['teeth']['uv']]), tex, soft, turns, size))
    Image.fromarray(np.concatenate(rows, 0)).save(path, quality=90)


def _preview_row(head, X, tri, uv, tex, soft, turns, size):
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
    return np.concatenate(tiles, 1)


def detect(rec, sheet_path, model, smile_at=None):
    """MediaPipe Face Landmarker's 478 points on each view that shows the face (sheet pixels),
    read on the view's quadrant at twice its size; and on the record's picture of the smile,
    where it names one and the picture is handed over (pixels of its levelled cut)."""
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
    spec = rec.get('smile_view')
    if spec and smile_at:
        cut = smile_picture(spec, smile_at)
        r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(np.asarray(cut))))
        if not r.face_landmarks:
            sys.exit(f"{rec['person_id']}: no face found in the picture of the smile")
        spec['points_px'] = [[round(l.x * cut.width, 1), round(l.y * cut.height, 1)] for l in r.face_landmarks[0]]
    det.close()


def front_path(person):
    return OUT_DIR / f'{person}_front.jpg'


def write_front(person, layer):
    """The front picture's file: the picture's square, and beside it where it is shown and,
    under that, where it shows hair (coded as the sheet's own blocks are, so a reader that
    decodes colours gets the shares themselves)."""
    from PIL import Image
    img, n = layer['image'].copy(), FRONT['px']
    img[:, n:] = linear_to_srgb(img[:, n:])
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(front_path(person), quality=JPEG_QUALITY, subsampling=0, optimize=True)


def front_layout():
    n, na = FRONT['px'], FRONT['alpha_px']
    return {'size_px': [n + na, n], 'colour_px': [0, 0, n, n], 'shown_px': [n, 0, n + na, na], 'kind_px': [n, na, n + na, 2 * na]}


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
        # ...and, where it stands out at all, the cells of the sheet it stands out in (rows of
        # `FINE_CELL_PX` cells, a bit a cell, the first cell a byte's high bit, base64): there
        # the renderer splits the skin's triangles down to `edge_m`, as `refine` did here.
        'grow': {'reach_m': round(grown['max_m'], 4), 'from_m': [round(float(x), 4) for x in grown['mid']], 'axis_m': GROW_AXIS_M,
                 'normal_px': list(SHAPE_PX), 'read': grown['read'],
                 **({'fine': {'cell_px': FINE_CELL_PX, 'edge_m': FINE_EDGE_M,
                              'cells': base64.b64encode(np.packbits(grown['cells'].ravel()).tobytes()).decode()}} if grown['max_m'] > 0 else {})},
        # How far the lids rest shut, so the eyes open as the front picture's do (0: as fitted).
        **({'lids': grown['lids']} if grown['lids'] else {}),
        # Each eye's own iris from the front picture (two squares side by side, the body's left
        # eye first), and the colour of the whites (sRGB).
        **({'eyes': {'px': list(EYES['px']), 'size': EYES['size'], 'white_srgb': [round(float(c), 3) for c in grown['eyes']['white']],
                     'iris_px': [round(r, 1) for r in grown['eyes']['iris_px']]}} if grown.get('eyes') else {}),
        # A front picture whose mouth is open (T-3553): the smile fitted to it (its file, each
        # expression unit's share on the body's left and right, how nearly the smiling face's
        # opening is the picture's, and how far the face's other points lie from the picture's,
        # rms, before and after), and the teeth behind the lips: a strip of `grid` points
        # (across, then down; rows from the top), each where it stands (metres, the body's rest
        # frame) and where on the body's map its colour is (the patch at `px` of the sheet),
        # carried by the bone `bone`; `shown` is the share of the opening the front camera
        # sees the strip in.
        **({'smile': {'file': str(smile_path(person).relative_to(ROOT)), 'sha256': sha256(smile_path(person)),
                      'units': grown['smile']['units'], 'vertices': int(len(grown['smile']['vertices'])), 'most_m': grown['smile']['most_m'],
                      'opening': grown['smile']['measured'], 'face': grown['smile']['face'],
                      # a smile fitted to a picture of its own (`smile_view`): that picture's camera,
                      # and what its teeth were multiplied by to stand in the sheet's light
                      # (`laid_on`: by how many points it was laid on the fitted face at rest, how far
                      # they lay from it before, and the furthest any point of the picture was moved)
                      **({k: grown['smile'][k] for k in ('camera', 'laid_on', 'tone') if k in grown['smile']})},
            'teeth': {'px': list(TEETH['px']), 'grid': list(TEETH['grid']), 'bone': 'head', 'shown': grown['teeth']['shown'],
                      'at_m': [[round(float(c), 5) for c in q] for q in grown['teeth']['at']],
                      'uv': [[round(float(c), 5) for c in q] for q in grown['teeth']['uv']]}} if grown.get('smile') else {}),
        # The front picture as a picture (`front_layer`), which the renderer shows from the front
        # where the sheet took another picture: its file, the picture's square and the square
        # that says where it is shown (pixels of the file), the picture's across and down (0..1)
        # from a place in the body's rest frame (metres; three numbers to multiply by, one to
        # add), the line it was taken along, and the share of the square it is shown in.
        'front': {'file': str(front_path(person).relative_to(ROOT)), 'sha256': sha256(front_path(person)), 'bytes': front_path(person).stat().st_size,
                  **front_layout(), 'u': [round(c, 5) for c in grown['front']['u']], 'v': [round(c, 5) for c in grown['front']['v']],
                  'toward': [round(c, 5) for c in grown['front']['toward']], 'shown': round(grown['front']['shown'], 3)},
    }


def smile_path(person):
    return SMILES / f'{person}.json'


def write_smile(person, smile):
    """A person's smile as the renderer takes it (tools/human_variation_kit.py carries it into
    the persons file): the kit's vertices it moves and each one's move, in the kit's delta unit."""
    SMILES.mkdir(parents=True, exist_ok=True)
    smile_path(person).write_text(json.dumps({
        'format': SMILE_FORMAT, 'ticket': 'T-3553', 'person_id': person, 'generated_by': 'tools/bake_likeness_skin.py',
        '_doc': ("The smile a picture of this person's own shows (the record's `smile_view`), fitted to it once the picture was laid on the fitted face at rest (read_smile_view, fit_smile): a move of the kit's vertices from the fitted face, mouth shut, which the figure rests as." if 'laid_on' in smile else "The smile this person's front picture shows, fitted to it as the picture was baked onto the face (fit_smile): a move of the kit's vertices from the fitted face, mouth shut, which the figure rests as.") + " The whole face moves: the lips onto the picture's, and the cheeks, the nose's wings and the lids onto the detector's points for them (`face`: how far those lie from the picture's, rms, at rest and smiling). Reconstructed, like the skin sheet it belongs to: a stand-in's smile on a fitted face. A reading; bake again, never edit.",
        'fit_values_sha256': values_sha(person), 'unit_m': SMILE_UNIT_M, 'units': smile['units'], 'opening': smile['measured'], 'face': smile['face'],
        'vertices': [int(i) for i in smile['vertices']], 'delta': [int(c) for c in smile['moves'].ravel()]}, separators=(',', ':')) + '\n')


def run(person, sheet_path, model=None, preview_path=None, smile_at=None):
    from PIL import Image
    path = SKINS / f'{person}.json'
    rec = json.loads(path.read_text())
    if rec['sheet'].get('sha256') and sha256(sheet_path) != rec['sheet']['sha256']:
        sys.exit(f"{person}: {sheet_path} is not the sheet the record names (SHA-256 differs)")
    if model:
        detect(rec, sheet_path, model, smile_at)
    sheet = np.asarray(Image.open(sheet_path).convert('RGB')).astype(np.float32) / 255
    head = fitted_head(person)
    tex, soft, tone, cams, grown = bake(rec, sheet, head, smile_at)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f'{person}_skin.jpg'
    compose(tex, soft, grown).save(out, quality=JPEG_QUALITY, subsampling=0, optimize=True)
    write_front(person, grown['front'])
    rec['sheet']['sha256'] = sha256(sheet_path)
    rec['cameras'] = cams
    rec['fit_values_sha256'] = values_sha(person)
    if grown.get('smile'):
        write_smile(person, grown['smile'])
    elif smile_path(person).exists():
        smile_path(person).unlink()
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
        if g.get('normal_px') != list(SHAPE_PX) or not (0 <= g.get('reach_m', -1) < 0.2) or len(g.get('from_m') or []) != 3 or g.get('axis_m') != GROW_AXIS_M:
            bad.append(f'{person}: the hair\'s standing out is not recorded as this tool records it; bake again')
        fine = g.get('fine')
        if g.get('reach_m', 0) > 0 and not (isinstance(fine, dict) and fine.get('cell_px') == FINE_CELL_PX and fine.get('edge_m') == FINE_EDGE_M
                                            and len(base64.b64decode(fine.get('cells', ''))) * 8 == (TEXTURE_PX[0] // FINE_CELL_PX) * (TEXTURE_PX[1] // FINE_CELL_PX)):
            bad.append(f'{person}: where the hair stands out is not recorded as this tool records it; bake again')
        lids = t.get('lids')
        if lids is not None and not (0 <= lids.get('rest', -1) <= LID_REST_MOST):
            bad.append(f'{person}: the lids\' rest is not one this tool gives; bake again')
        e = t.get('eyes')
        if e is not None and (e.get('px') != list(EYES['px']) or e.get('size') != EYES['size']
                              or not (isinstance(e.get('white_srgb'), list) and len(e['white_srgb']) == 3 and all(0 < x < 1 for x in e['white_srgb']))):
            bad.append(f'{person}: the eyes are not recorded as this tool records them; bake again')
        opens = any(v.get('mouth') == 'open' for v in rec['views']) or bool(rec.get('smile_view'))
        sv = rec.get('smile_view')
        if sv is not None and not (re.fullmatch(r'[0-9a-f]{64}', str(sv.get('sha256', ''))) and len(sv.get('crop_px') or []) == 4
                                   and isinstance(sv.get('level_deg'), (int, float)) and len(sv.get('points_px') or []) == 478):
            bad.append(f"{person}: the picture of the smile is not recorded as this tool reads it")
        teeth, smile = t.get('teeth'), t.get('smile')
        if opens != bool(teeth) or opens != bool(smile) or opens != smile_path(person).exists():
            bad.append(f"{person}: a smile and its teeth are not both recorded, or are recorded for a mouth that is shut; bake again")
        elif opens:
            n = TEETH['grid'][0] * TEETH['grid'][1]
            (u0, v0, u1, v1), (rx0, ry0, rx1, ry1) = RECTS[0]['uv'], RECTS[0]['px']
            x0, y0, x1, y1 = TEETH['px']
            box = (u0 + (x0 - rx0) / (rx1 - rx0) * (u1 - u0), v0 + (y0 - ry0) / (ry1 - ry0) * (v1 - v0),
                   u0 + (x1 - rx0) / (rx1 - rx0) * (u1 - u0), v0 + (y1 - ry0) / (ry1 - ry0) * (v1 - v0))
            if (teeth.get('px') != list(TEETH['px']) or teeth.get('grid') != list(TEETH['grid']) or teeth.get('bone') != 'head'
                    or len(teeth.get('at_m') or []) != n or len(teeth.get('uv') or []) != n or not teeth.get('shown', 0) >= TEETH['shown']
                    or not all(box[0] < u < box[2] and box[1] < w < box[3] for u, w in teeth['uv'])):
                bad.append(f"{person}: the teeth are not recorded as this tool records them; bake again")
            mouth = smile.get('opening') or {}
            if not (mouth.get('edge_off_mm', 99) <= MOUTH_HOLDS[0] and mouth.get('ring_off_mm', 99) <= MOUTH_HOLDS[1]):
                bad.append(f"{person}: the recorded smile does not open as its front picture's mouth does ({mouth})")
            face = smile.get('face') or {}
            if not face.get('off_mm', 99) <= min(SMILE_FACE_HOLDS_MM, face.get('rest_off_mm', 0)):
                bad.append(f"{person}: the recorded smile does not carry the rest of the face to its front picture ({face}); bake again")
            kept = json.loads(smile_path(person).read_text())
            units = json.loads(F.AXES.read_text())['expressions']['units']
            if (sha256(smile_path(person)) != smile.get('sha256') or kept.get('format') != SMILE_FORMAT or kept.get('unit_m') != SMILE_UNIT_M
                    or kept.get('fit_values_sha256') != values_sha(person) or len(kept.get('delta') or []) != 3 * len(kept.get('vertices') or [1])
                    or sorted(kept.get('units') or {}) != sorted(pathlib.PurePosixPath(u).stem for u in units)
                    or not all(0 <= w <= SMILE_MOST + 1e-6 for pair in kept['units'].values() for w in pair)):
                bad.append(f"{person}: {smile_path(person).relative_to(ROOT)} is not the smile this skin was baked with; bake again")
        fr = t.get('front') or {}
        if (any(fr.get(k) != v for k, v in front_layout().items()) or not all(isinstance(fr.get(k), list) and len(fr[k]) == m for k, m in (('u', 4), ('v', 4), ('toward', 3)))
                or abs(float(np.linalg.norm(fr['toward'])) - 1) > 1e-3 or not 0 < fr.get('shown', 0) < 1):
            bad.append(f'{person}: the front picture is not recorded as this tool records it; bake again')
        elif not (ROOT / fr['file']).exists() or sha256(ROOT / fr['file']) != fr.get('sha256'):
            bad.append(f"{person}: {fr['file']} is not the front picture the record baked (missing, or its SHA-256 differs)")
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
    # The renderer moves the skin out along the same line the bake measured along, and splits it as finely.
    js = (ROOT / 'renderers/web/js/human-skin.js').read_text()
    for needs in ('from.y = clamp( vChiSkinP.y, from.y - chiLikeAxis, from.y );', 'g.axis_m > 0 ? g.axis_m : 0', 'fineCells(g.fine, skin.size_px)',
                  'teethStrip(skin.teeth)', f'MOUTH_SHADE = Object.freeze({{ u0: {MOUTH_SHADE_U0}, u1: {MOUTH_BAG_UV[2]}, v0: {MOUTH_BAG_UV[1]},', 'float bag = step( ${MOUTH_SHADE.u0}, vMapUv.x )',
                  'vChiLikeFront = vec2( dot( chiLikeFrontU.xyz, chiGrown ) + chiLikeFrontU.w, dot( chiLikeFrontV.xyz, chiGrown ) + chiLikeFrontV.w );',
                  'front: grows ? frontPicture(skin.front) : null', 'four(front.colour_px) || !four(front.shown_px) || !four(front.kind_px)'):
        if needs not in js:
            bad.append(f'renderers/web/js/human-skin.js no longer reads the record as this tool writes it: {needs}')
    for b in bad:
        print('FAIL', b)
    if bad:
        sys.exit(1)
    print(f'likeness skins: {len(list(SKINS.glob("*.json")))} records hold')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('person', nargs='?')
    ap.add_argument('--sheet')
    ap.add_argument('--smile', metavar='PICTURE', help="the record's own picture of the smile (`smile_view`), where it names one")
    ap.add_argument('--detect', metavar='MODEL')
    ap.add_argument('--preview', metavar='OUT')
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    if args.check:
        return check()
    if not args.person or not args.sheet:
        ap.error('PERSON and --sheet, or --check')
    run(args.person, args.sheet, args.detect, args.preview, args.smile)


if __name__ == '__main__':
    main()
