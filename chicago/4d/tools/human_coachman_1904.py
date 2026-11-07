# SPDX-License-Identifier: GPL-3.0-or-later
"""A 1904 private coachman's standing livery on the shared portable male rig (T-3483).

First worn by Charles Nelson (born 1848 in Sweden), the Glessners' coachman, who lived with
his family in the rear building behind 1800 Prairie Avenue in 1900. Hans Johnson, the Otis
family's coachman (T-3409), is dressed for the box: a box coat with a shoulder cape. Charles
is drawn on foot at his own stable doors, in the livery a coachman stood in, read from the
plates of Mrs. Seely's Cook Book (New York, 1902; recipe data/humans/recipes/
coachman_livery_1904.json):

  livery coat   a long double-breasted coat buttoned to the throat and falling straight to
                the knee, a low turned collar (the 'Coachman' plate; the Griffith 1905
                coachmen wear double-breasted coats with stand collars)
  buttons       two rows of six bright buttons from the chest to the waist, the rows a
                little wider apart at the top (the plate; white metal is our choice, where
                Hans wears brass)
  stock         a white stock standing above the coat collar (the plate; Rau 1902)
  gloves        white gloves (the plate)
  breeches      white, showing a hand's breadth between the coat's hem and the boots
                (the plate)
  top boots     plain black boots to just below the knee (the plate)
  top hat       a tall silk hat with a narrow curled brim (the plate; every coachman of the
                coachman_1904 set). A separate mesh rigid on the head bone.

Generated geometry is CC0-1.0. Cuts, eases, lengths and colours are reconstructed (the
plates are monochrome); liberty L-human-modular-dress-1789 with its T-3483 supplement. The
source anatomy is never changed: every piece is a shell offset from the body's own
triangles (its UVs and skin weights carried) or a loft round the body's own sections,
skinned to the body's own bones. Reuses the 1904 gentleman's and the 1835 merchant's
helpers, lending them this outfit's measures only for the call (their own builds are
untouched).

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_coachman_assembly() and makes the four LODs.
"""
from __future__ import annotations
import contextlib
import copy
import hashlib
import json
import math
from pathlib import Path

from human_dress_components import need, digest, empty
from human_period_wardrobe import finish_edges
from human_workwear_fit import _slab_points
import human_gentleman_1904 as G
import human_merchant_1835 as M

BODY_SHA256 = 'ef5eb3ca282b29c482a67af4e3e50d1ed29a8055eed0230ee2a58ec36dddbba9'
ASSEMBLY = 'coachman_livery_1904_v1'
RECIPE = 'data/humans/recipes/coachman_livery_1904.json'
LIBERTY = 'L-human-modular-dress-1789'

# Every dimension of the outfit, in metres; the recipe repeats them for review and the
# builder refuses a recipe that disagrees. All are reconstructed choices.
TAILORING = dict(
    coat=dict(ease=.026, armpit_extra=.022, sleeve_short_of_wrist=.026, collar_above_neck=.030, waist_below_spine02=.020,
              roll_above_spine02=.345, v_half_width_top=.030),
    skirt=dict(hem_y=.500, ease=.036, front_gap_deg=.5, segments=72, rows=14),
    buttons=dict(radius=.0095, count=6, top_above_spine02=.300, bottom_above_spine02=.020, x_top=.088, x_bottom=.064,
                 standoff=.003, sides=10),
    stock=dict(ease=.006, bottom_below_neck=.030, back_bottom_below_neck=.004, back_above_neck=.050, jaw_clearance=.006,
               segments=40, rows=6),
    gloves=dict(ease=.0022, above_wrist=.030),
    breeches=dict(ease=.010, waist_height_fraction=.585, bottom_y=.400, thigh_fullness=.014, smoothing=20),
    boots=dict(bottom_y=.080, top_y=.430, ease_bottom=.006, ease_top=.018, segments=28, rows=12),
    top_hat=dict(seat_below_top=.084, ease=.007, crown_height=.165, crown_flare=1.05, brim_side=.036, brim_fore=.050,
                 brim_curl=.020, thickness=.004),
)

MATERIALS = {
    'garment_outer__livery_coat_green_1904': {'base_color_linear': [.014, .026, .019, 1], 'roughness': .86},
    'accessory__white_metal_livery_buttons': {'base_color_linear': [.62, .62, .60, 1], 'roughness': .32},
    'garment_upper__white_stock_1904': {'base_color_linear': [.80, .80, .78, 1], 'roughness': .7},
    'accessory__white_cotton_gloves': {'base_color_linear': [.72, .71, .68, 1], 'roughness': .85},
    'garment_lower__breeches_white_1904': {'base_color_linear': [.66, .64, .58, 1], 'roughness': .86},
    'footwear__black_top_boots': {'base_color_linear': [.010, .010, .010, 1], 'roughness': .32},
    'headwear__silk_top_hat_1904': {'base_color_linear': [.014, .014, .016, 1], 'roughness': .40},
}
SHOE_MATERIAL = 'footwear__black_top_boots'
WEAVE_MATERIAL = 'garment_upper__white_stock_1904'


@contextlib.contextmanager
def _lent(module, **parts):
    """Lend `module` this outfit's measures for one call, then give its own back."""
    saved = {k: module.TAILORING[k] for k in parts}
    try:
        module.TAILORING.update(parts)
        yield
    finally:
        module.TAILORING.update(saved)


def livery_coat(body, bones):
    """The coat above its waist seam: closed and buttoned to the throat, where a short V
    shows the stock, a low collar standing round the neck; sleeves to the glove. Then its
    skirt, lofted from the seam to the knee round the body's own sections, closed in front."""
    t = TAILORING
    with _lent(G, coat=dict(t['coat'], lapel_width=.05, lapel_notch=.8), skirt=t['skirt']):
        coat, roll = G.coat_body(body, bones)
        skirt = G.coat_skirt(body, bones, coat, roll[0])
    material = 'garment_outer__livery_coat_green_1904'
    coat = finish_edges(coat, .0018)
    coat['name'] = 'livery_coat_body'; coat['material'] = material
    coat['receipt'] = dict(coat['receipt'], garment='double-breasted livery coat, buttoned to the throat')
    skirt['name'] = 'livery_coat_skirt'; skirt['material'] = material
    skirt['receipt'] = dict(skirt['receipt'], garment='livery coat skirt to the knee, closed in front')
    return coat, skirt, roll


def buttons(coat, bones):
    """Two rows of six bright buttons laid on the coat's closed front, the rows converging
    a little from the chest to the waist, skinned as the coat beneath them."""
    t = TAILORING['buttons']
    spine = bones['spine_02']['head_m'][1]
    top, bottom = spine+t['top_above_spine02'], spine+t['bottom_above_spine02']
    out = empty('livery_buttons', 'accessory__white_metal_livery_buttons')
    n = t['sides']; placed = 0
    for row in range(t['count']):
        f = row/(t['count']-1)
        y = top+(bottom-top)*f
        xr = t['x_top']+(t['x_bottom']-t['x_top'])*f
        for sign in (1, -1):
            x0 = sign*xr
            z0, w = G._surface_sample(coat, x0, y)
            c = len(out['positions_m']); placed += 1
            out['positions_m'].append([x0, y, z0+t['standoff']+.0018]); out['uvs'].append([.5, .5]); out['weights'].append(w)
            for k in range(n):
                a = 2*math.pi*k/n
                x, yy = x0+t['radius']*math.cos(a), y+t['radius']*math.sin(a)
                try:
                    z, _ = G._surface_sample(coat, x, yy)
                except ValueError:
                    z = z0
                out['positions_m'].append([x, yy, z+t['standoff']]); out['uvs'].append([.5+.5*math.cos(a), .5+.5*math.sin(a)])
                out['weights'].append(w)
            for k in range(n):
                out['triangles'].append([c, c+1+k, c+1+(k+1) % n])
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='white-metal livery buttons, two rows', count=placed, radius_m=t['radius'],
                          rows_y_m=[top, bottom], half_spacing_m=[t['x_top'], t['x_bottom']])
    return out


def stock(body, bones):
    """A white stock round the neck, standing above the coat's collar (the merchant's stock,
    cut lower and in white linen)."""
    with _lent(M, stock=TAILORING['stock']):
        out, _frame = M.stock(body, bones)
    out['name'] = 'white_stock'; out['material'] = 'garment_upper__white_stock_1904'
    out['receipt'] = dict(out['receipt'], garment='white linen stock')
    return out


def _hand_mass(v):
    return math.fsum(x for b, x in v['w'].items()
                     if b.startswith(('hand', 'thumb', 'index', 'middle', 'ring', 'pinky')))


def gloves(body, bones):
    """White gloves: the body's own hands and a little of the wrist, offset as a thin shell
    and skinned as the hand, so the fingers close in them."""
    t = TAILORING['gloves']
    wrist = abs(bones['hand_l']['head_m'][0])-t['above_wrist']
    fields = [lambda v: abs(v['p'][0])-wrist]
    out = G._poly_shell(body, bones, 'white_gloves', 'accessory__white_cotton_gloves', fields, t['ease'], [],
                        bones['neck_01']['head_m'][1])
    out = finish_edges(out, .0010)
    out['receipt'] = dict(garment='white cotton gloves', cuff_x_m=wrist, ease_m=t['ease'])
    return out


def breeches(body, bones, height):
    """White breeches from the waist to below the knee: the body's own legs and seat offset
    and smoothed over the fork, a little fuller over the thigh, ending inside the boot tops."""
    t = TAILORING['breeches']
    waist = t['waist_height_fraction']*height
    fields = [lambda v: waist-v['p'][1], lambda v: v['p'][1]-t['bottom_y'], lambda v: .35-G._arm_mass(v)]
    out = G._poly_shell(body, bones, 'white_breeches', 'garment_lower__breeches_white_1904', fields, t['ease'],
                        [(t['bottom_y'], waist)], bones['neck_01']['head_m'][1], smooth=(t['smoothing'], t['ease']))
    knee = bones['calf_l']['head_m'][1]
    full = 0
    for i, p in enumerate(out['positions_m']):
        # Riding breeches stand out over the thigh and close in at the knee.
        lo, hi = knee+.04, waist-.12
        if not lo < p[1] < hi:
            continue
        g = math.sin(math.pi*(p[1]-lo)/(hi-lo))
        n = out['_normals'][i]
        out['positions_m'][i] = [p[a]+t['thigh_fullness']*g*n[a] for a in range(3)]
        full += 1
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='white breeches to below the knee', waist_y_m=waist, bottom_y_m=t['bottom_y'],
                          ease_m=t['ease'], thigh_points_eased=full)
    return out


def top_boots(body, bones):
    """Plain black top boots: for each leg a loft from the ankle to just below the knee,
    every ring enclosing the leg's own section (and the breeches' foot) with more room at
    the top, skinned as the nearest point of the leg beneath it."""
    t = TAILORING['boots']
    m = body['meshes'][0]
    P, W = m['positions_m'], m['weights']
    out = empty('top_boot_shafts', SHOE_MATERIAL)
    n, rows = t['segments'], t['rows']
    dirs = [(math.sin(2*math.pi*k/n), math.cos(2*math.pi*k/n)) for k in range(n)]
    levels = [t['bottom_y']+(t['top_y']-t['bottom_y'])*r/(rows-1) for r in range(rows)]
    for side in ('l', 'r'):
        sign = 1 if side == 'l' else -1
        leg = [i for i, (p, w) in enumerate(zip(P, W))
               if sign*p[0] > .02 and p[1] <= t['top_y']+.04 and
               math.fsum(x for b, x in w.items() if b.endswith('_'+side)) > .5]
        tris = [[P[i] for i in f] for f in m['triangles'] if all(sign*P[i][0] > .02 for i in f)
                and min(P[i][1] for i in f) <= t['top_y']+.02 and max(P[i][1] for i in f) >= t['bottom_y']-.02]
        cx = bones[f'calf_{side}']['head_m'][0]; cz = bones[f'calf_{side}']['head_m'][2]
        base = len(out['positions_m'])
        supports = []
        for r, y in enumerate(levels):
            pts = _slab_points(tris, y-.015, y+.015)
            need(len(pts) >= 3, f'no leg section for the {side} boot at {y:.3f}')
            supports.append([max((p[0]-cx)*dx+(p[2]-cz)*dz for p in pts) for dx, dz in dirs])
        # A boot shaft is a stiff tube: no ring narrower than 92 per cent of the one below
        # it toward the calf, smoothed round.
        for r in range(1, rows):
            supports[r] = [max(a, .92*b) for a, b in zip(supports[r], supports[r-1])]
        for r, y in enumerate(levels):
            s = supports[r]
            s = [max(s[k], (s[k-1]+2*s[k]+s[(k+1) % n])/4) for k in range(n)]
            f = r/(rows-1)
            ease = t['ease_bottom']+(t['ease_top']-t['ease_bottom'])*f*f
            for k, (dx, dz) in enumerate(dirs):
                q = [cx+(s[k]+ease)*dx, y, cz+(s[k]+ease)*dz]
                near = min(leg, key=lambda i: (P[i][0]-q[0])**2+(P[i][1]-q[1])**2+(P[i][2]-q[2])**2)
                out['positions_m'].append(q); out['uvs'].append([k/n, f]); out['weights'].append(G._skin4(W[near], 1.))
        for r in range(rows-1):
            for k in range(n):
                a = base+r*n+k; b = base+r*n+(k+1) % n; c = a+n; d = b+n
                faces = ([a, b, d], [a, d, c]) if sign > 0 else ([a, b, d], [a, d, c])
                out['triangles'] += list(faces)
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out = finish_edges(out, .0018)
    out['receipt'] = dict(garment='black top boot shafts to below the knee', bottom_y_m=t['bottom_y'], top_y_m=t['top_y'],
                          ease_m=[t['ease_bottom'], t['ease_top']], skinning='nearest leg point of its own side')
    return out


def top_hat(body, bones):
    with _lent(M, top_hat=TAILORING['top_hat']):
        out = M.top_hat(body, bones)
    out['name'] = 'headwear_top_hat'; out['material'] = 'headwear__silk_top_hat_1904'
    out['receipt'] = dict(out['receipt'], garment='silk top hat')
    return out


def construct(body):
    before = digest(body)
    bones = {b['name']: b for b in body['skeleton']}
    height = max(p[1] for m in body['meshes'] for p in m['positions_m'])
    coat, skirt, roll = livery_coat(body, bones)
    parts = [stock(body, bones), coat, skirt, buttons(coat, bones), gloves(body, bones), breeches(body, bones, height),
             top_boots(body, bones), top_hat(body, bones)]
    for m in parts:
        m.pop('_normals', None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_coachman_livery_1904_source_v1', license='CC0-1.0', units='m', up_axis='+Y',
                forward_axis='+Z', grade='reconstructed', assembly=ASSEMBLY, body_sha256=BODY_SHA256,
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts,
                materials=copy.deepcopy(MATERIALS), shoe_material=SHOE_MATERIAL, weave_material=WEAVE_MATERIAL,
                tailoring=copy.deepcopy(TAILORING),
                limitations=['Cut, ease, lengths, folds and colours are reconstructed; the plates are monochrome and of New York',
                             'No cloth simulation: shells and the skirt follow the body bones',
                             'Boot shafts are stiff lofts skinned to the leg; the foot is the shared fitted shoe',
                             'Hat rigid on the head bone'])


def prepare_coachman_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer for T-3483; never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('coachman_components', {})
    need(spec.get('version') == 1 and spec.get('generator') == 'tools/human_coachman_1904.py',
         'unsupported coachman component generator')
    need(variant.get('recipe_path') == RECIPE and variant.get('component_assembly') == ASSEMBLY,
         'coachman assembly is bound to its own recipe')
    need(recipe.get('scene_date') == '1904-07-01' and recipe.get('grade') == 'reconstructed',
         'coachman scene/appearance grade changed')
    need(spec.get('tailoring') == TAILORING, 'recipe tailoring differs from the generator')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256 == spec.get('body_sha256'), 'unreviewed coachman body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(spec.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'coachman components require the declared liberty')
    for garment in spec['garments']:
        prov = garment.get('provenance', {})
        need(prov.get('grade') in ('attested', 'inferred', 'reconstructed') and (prov.get('source_ids') or prov.get('liberty')),
             f"garment {garment.get('id')} has no provenance")
        for sid in prov.get('source_ids', []):
            record = json.loads((root/'data/sources'/f'{sid}.json').read_text())
            need(record.get('id') == sid and record.get('rights_status') in ('public_domain', 'no_known_restrictions'),
                 f'{sid}: not a cleared reference')
    for sid in recipe['sources']:
        need((root/'data/sources'/f'{sid}.json').is_file(), f'{sid}: no source record')
    bundle = construct(body)
    bundle['liberty'] = LIBERTY
    bundle['garments'] = [{'id': g['id'], 'material': g['material'], 'provenance': g['provenance']} for g in spec['garments']]
    for material, m in bundle['materials'].items():
        need(recipe['colors_linear_rgba'].get(material) == m['base_color_linear'], f'{material}: recipe/source colour differs')
    names = {b['name'] for b in body['skeleton']}
    for mesh in bundle['meshes']:
        count = len(mesh['positions_m'])
        need(mesh['material'] in bundle['materials'], f"{mesh['name']}: material outside the outfit")
        need(count > 0 and count == len(mesh['weights']) == len(mesh['uvs']), 'incomplete garment arrays')
        need(len(mesh['corner_uvs']) == len(mesh['triangles']), 'garment corner UVs missing')
        for mapping in mesh['weights']:
            need(1 <= len(mapping) <= 4 and not (set(mapping)-names)
                 and all(math.isfinite(w) and w >= 0 for w in mapping.values())
                 and abs(math.fsum(mapping.values())-1.) < 1e-9, 'invalid garment skin')
        for face in mesh['triangles']:
            need(len(face) == len(set(face)) == 3 and all(type(i) is int and 0 <= i < count for i in face),
                 'invalid garment triangle')
    return bundle


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(); p.add_argument('--body', type=Path, required=True)
    a = p.parse_args(); raw = a.body.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256, 'unreviewed body source')
    data = construct(json.loads(raw))
    print(json.dumps({'meshes': [{'name': m['name'], 'material': m['material'], 'vertices': len(m['positions_m']),
                                  'triangles': len(m['triangles']), 'receipt': m.get('receipt')} for m in data['meshes']]},
                     indent=1, default=str))
