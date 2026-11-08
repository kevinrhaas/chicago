# SPDX-License-Identifier: GPL-3.0-or-later
"""An 1812 engage of the Chicago trading households on the shared portable male rig.

An anonymous French Canadian or Metis engage (a hired man under engagement to a trader:
boatman, carrier, labourer) of John Kinzie's or another trading household at Chicago in
August 1812. Wau-Bun names the dress once for Chicago in 1812: the Kinzie family hid a
sergeant on 16 August by dressing him "in a suit of deer-skin, with belt, moccasins, and
pipe, like a French engage" (kinzie_waubun_1856, ch. XIX). The pieces, read from that and
from the period texts in the recipe (data/humans/recipes/engage_1812.json):

  shirt        printed cotton (calico), coloured, full sleeves, open at the throat, tucked
               in: Wau-Bun's boatmen of 1830 and the "mitiff" whose "calico shirt,
               bright-colored scarf around his waist" is "the usual dress of his class";
               Hubbard's calico shirt (1818); Heriot's issue of a shirt to each canoeman
               (1807). The labourer's shirt of 1835 is reused (tools/human_labourer_1835.py).
  sash         a worsted sash wound twice round the waist and knotted at the left hip, its
               two ends hanging (Lambert's "worsted sash of various colours", 1810; Wau-Bun's
               "belt" and "scarf around his waist")
  trousers     deer-skin, full and straight to the instep (Wau-Bun's "suit of deer-skin";
               Heriot's trousers), on the labourer's trouser shell
  cap          a red knitted cap, its soft top falling over to the back (Wau-Bun's "bonnet
               rouge, or tuque as the voyageurs call it"; Lambert's red cap "worn the whole
               year round"; Heriot's worsted caps "knitted with wires"), rigid on the head
  moccasins    smoked deer-skin, the shared closed foot loft (Wau-Bun 1812; Lambert:
               moccasins "in general use among the country people, as shoes")

Generated geometry is CC0-1.0. Cuts, eases, lengths and colours are reconstructed; liberty
L-human-modular-dress-1789 with the supplement proposed in
docs/RESEARCH/people-1812-dress/engage-native-men.md. The source anatomy is never changed.

The loft helpers here (`supports`, `loft`, `band`, `nearest_weights`) are shared with the
Potawatomi man's dress (tools/human_potawatomi_man_1812.py).

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_engage_assembly() through the recipe's `role_1812`.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path

from human_dress_components import need, digest, empty, leg_follow
from human_period_wardrobe import finish_edges
from human_workwear_fit import _slab_points
import human_gentleman_1904 as G
import human_labourer_1835 as L

BODY_SHA256 = 'ef5eb3ca282b29c482a67af4e3e50d1ed29a8055eed0230ee2a58ec36dddbba9'
ASSEMBLY = 'engage_1812_v1'
RECIPE = 'data/humans/recipes/engage_1812.json'
LIBERTY = 'L-human-modular-dress-1789'
PERSON = 'anonymous_engage_1812'

# Every dimension of the outfit, in metres; the recipe repeats them for review and the
# builder refuses a recipe that disagrees. All are reconstructed choices. The shirt and
# the trousers are the 1835 labourer's own cut (his TAILORING, held equal here).
TAILORING = dict(
    shirt=copy.deepcopy(L.TAILORING['shirt']),
    trousers=copy.deepcopy(L.TAILORING['trousers']),
    sash=dict(bottom_y=.985, top_y=1.070, ease=.005, segments=48, rows=6, roll=.003, knot_deg=68.,
              end_width=.085, end_lengths=(.30, .23), end_gap=.03, end_out=.010, end_rows=8),
    tuque=dict(seat_below_top=.088, ease=.009, cuff=.030, cuff_thickness=.005, segments=28, fitted_rows=4,
               crown_below_top=.022, tail_rows=12, tail_rise=.075, tail_back=.075, tail_drop=.075, tail_radius=.020),
)

MATERIALS = {
    'garment_upper__shirt_calico_blue_1812': {'base_color_linear': [.10, .15, .29, 1], 'roughness': .86},
    'garment_lower__trousers_deerskin_1812': {'base_color_linear': [.25, .165, .095, 1], 'roughness': .9},
    'accessory__sash_worsted_red_1812': {'base_color_linear': [.30, .045, .032, 1], 'roughness': .9},
    'headwear__tuque_red_1812': {'base_color_linear': [.33, .045, .035, 1], 'roughness': .92},
    'footwear__moccasins_smoked_1812': {'base_color_linear': [.14, .088, .048, 1], 'roughness': .88},
}
SHOE_MATERIAL = 'footwear__moccasins_smoked_1812'
WEAVE_MATERIAL = 'garment_upper__shirt_calico_blue_1812'


# --- loft helpers (shared with the Potawatomi man) --------------------------------------

def directions(n, offset=.5):
    return [(math.sin(2*math.pi*(k+offset)/n), math.cos(2*math.pi*(k+offset)/n)) for k in range(n)]


def supports(triangles, levels, dirs, ease, hang=False, centre=(0., 0.)):
    """For each level, how far the sections of `triangles` reach in each direction about
    `centre` (x, z), plus `ease`: a convex polygon that encloses the whole slab between the
    neighbouring levels. With `hang`, below the widest level no ring is narrower than the
    one above it (cloth falls straight from the seat, it does not follow the thighs in)."""
    cx, cz = centre
    out = []
    for i in range(len(levels)):
        a = levels[max(0, i-1)]; b = levels[min(len(levels)-1, i+1)]
        pts = _slab_points(triangles, min(a, b)-.004, max(a, b)+.004)
        need(len(pts) >= 3, 'empty section for a loft')
        out.append([max((p[0]-cx)*dx+(p[2]-cz)*dz for p in pts)+ease for dx, dz in dirs])
    if hang:
        widest = max(range(len(levels)), key=lambda i: sum(out[i]))
        for i in range(widest+1, len(levels)):
            out[i] = [max(a, b) for a, b in zip(out[i], out[i-1])]
    return out


def ring_point(support_row, dirs, k, centre=(0., 0.)):
    """The corner of the support polygon between faces k-1 and k: a point on its boundary."""
    n = len(dirs)
    nx0, nz0 = dirs[(k-1) % n]; nx1, nz1 = dirs[k]
    a, b = support_row[(k-1) % n], support_row[k]
    det = nx0*nz1-nx1*nz0
    return centre[0]+(a*nz1-b*nz0)/det, centre[1]+(nx0*b-nx1*a)/det


def nearest_weights(body, lo, hi):
    """A function giving a point the skin weights of the nearest body point between y=lo
    and y=hi (the garment moves as the skin beneath it)."""
    src = body['meshes'][0]
    pool = [(p, w) for p, w in zip(src['positions_m'], src['weights']) if lo-.03 <= p[1] <= hi+.03]
    need(bool(pool), 'no body points for garment weights')
    def weights(p):
        best = min(pool, key=lambda q: (q[0][0]-p[0])**2+(q[0][1]-p[1])**2+(q[0][2]-p[2])**2)
        return G._skin4(dict(best[1]), 1.)
    return weights


def grid(out, rows, closed, weights_of):
    """Triangulate `rows` (lists of points) into `out`, closed round or open; UVs by index."""
    base = len(out['positions_m'])
    cols = len(rows[0])
    for i, row in enumerate(rows):
        for j, p in enumerate(row):
            out['positions_m'].append(list(p)); out['uvs'].append([j/max(1, cols-(0 if closed else 1)), i/max(1, len(rows)-1)])
            out['weights'].append(weights_of(p))
    span = cols if closed else cols-1
    for i in range(len(rows)-1):
        for j in range(span):
            a = base+i*cols+j; b = base+i*cols+(j+1) % cols; c = a+cols; d = b+cols
            for f in ([a, b, d], [a, d, c]):
                out['triangles'].append(f); out['corner_uvs'].append([out['uvs'][v] for v in f])
    return base


def band(triangles, lo, hi, rows, segments, ease, roll, name, material, weights_of):
    """A closed band of cloth round whatever `triangles` are (a body or the garments on it)
    from y=lo to y=hi, `ease` clear of their sections and swelling `roll` at its middle."""
    levels = [lo+(hi-lo)*i/(rows-1) for i in range(rows)]
    dirs = directions(segments)
    sup = supports(triangles, levels, dirs, ease)
    # One convex section for the whole band (a sash or a belt does not follow every hollow).
    top = [max(s[k] for s in sup) for k in range(segments)]
    out = empty(name, material)
    pts = []
    for i, y in enumerate(levels):
        f = i/(rows-1)
        row = []
        for k in range(segments):
            x, z = ring_point(top, dirs, k)
            r = math.hypot(x, z); g = 1+roll*math.sin(math.pi*f)/r
            row.append((x*g, y, z*g))
        pts.append(row)
    grid(out, pts, True, weights_of)
    out = finish_edges(out, .0015)
    out['receipt'] = dict(bottom_y_m=lo, top_y_m=hi, ease_m=ease, roll_m=roll, segments=segments)
    return out, top, dirs


# --- the engage's pieces ----------------------------------------------------------------

def shirt(body, bones):
    out = L.shirt(body, bones)
    out['name'] = 'shirt_calico'; out['material'] = 'garment_upper__shirt_calico_blue_1812'
    out['receipt']['garment'] = 'printed cotton shirt, full sleeves, open throat, tucked in (the 1835 labourer\'s cut)'
    return out


def trousers(body, bones, height):
    out = L.trousers(body, bones, height)
    out['name'] = 'deerskin_trousers'; out['material'] = 'garment_lower__trousers_deerskin_1812'
    return out


def _tris(*meshes):
    return [[m['positions_m'][i] for i in f] for m in meshes for f in m['triangles']]


def sash(body, bones, garments):
    """A worsted sash wound round the waist over the shirt and the trousers' top, and its
    two ends hanging from a knot at the left hip, the longer in front."""
    t = TAILORING['sash']
    waist = (t['bottom_y']+t['top_y'])/2
    body_w = nearest_weights(body, t['bottom_y'], t['top_y'])
    wrap, section, dirs = band(_tris(*garments), t['bottom_y'], t['top_y'], t['rows'], t['segments'], t['ease'],
                               t['roll'], 'sash_worsted', 'accessory__sash_worsted_red_1812', body_w)
    # The ends: two ribbons from the knot down over the left hip, each clear of the thigh's
    # own sections (with the trousers') as it falls, skinned from the pelvis into the thigh.
    follow = leg_follow(bones, waist)
    legs = _tris(body['meshes'][0], *garments)
    a0 = math.radians(t['knot_deg'])
    out = empty('sash_ends', 'accessory__sash_worsted_red_1812')
    for e, length in enumerate(t['end_lengths']):
        a = a0+(-1 if e == 0 else 1)*t['end_gap']/.17
        dx, dz = math.sin(a), math.cos(a); tx, tz = math.cos(a), -math.sin(a)
        top = t['bottom_y']+.035
        levels = [top-length*i/(t['end_rows']-1) for i in range(t['end_rows'])]
        reach = supports(legs, levels, [(dx, dz)], t['ease']+t['end_out']+.004*e, hang=True)
        r0 = max(section[k]*(dx*dirs[k][0]+dz*dirs[k][1]) for k in range(len(dirs)))
        rows = []
        for i, y in enumerate(levels):
            r = max(reach[i][0], r0+t['roll']+.004+.004*e)
            c = (dx*r, y, dz*r)
            half = t['end_width']/2*(1-.15*i/(t['end_rows']-1))
            rows.append([(c[0]-tx*half, y, c[2]-tz*half), (c[0], y, c[2]), (c[0]+tx*half, y, c[2]+tz*half)])
        grid(out, rows, False, lambda p: G._skin4(follow(p), 1.))
    out = finish_edges(out, .0018)
    wrap['receipt'].update(garment='worsted sash wound round the waist', knot_deg=t['knot_deg'])
    out['receipt'] = dict(garment='sash ends from the knot at the left hip', lengths_m=list(t['end_lengths']),
                          width_m=t['end_width'], skinning='pelvis into the left thigh (leg_follow)')
    return wrap, out


def tuque(body, bones, lod=0):
    """A red knitted cap: a close crown round the skull's own sections from a turned-up cuff
    over the brow, its soft top falling over to the back of the head. Rigid on the head."""
    t = TAILORING['tuque']
    P = body['meshes'][0]['positions_m']; W = body['meshes'][0]['weights']
    head_pts = [p for p, w in zip(P, W) if w.get('head', 0.) > .9]
    top = max(p[1] for p in head_pts)
    seat = top-t['seat_below_top']
    band_pts = [p for p in head_pts if seat-.012 <= p[1] <= seat+.03]
    cx = (min(p[0] for p in band_pts)+max(p[0] for p in band_pts))/2
    cz = (min(p[2] for p in band_pts)+max(p[2] for p in band_pts))/2
    n = t['segments']
    dirs = [(math.sin(2*math.pi*k/n), math.cos(2*math.pi*k/n)) for k in range(n)]
    def section(y, ease):
        sl = [p for p in head_pts if abs(p[1]-y) <= .006]
        if not sl:
            return None
        return [max((p[0]-cx)*dx+(p[2]-cz)*dz for p in sl)+ease for dx, dz in dirs]
    seat_r = section(seat, t['ease'])
    seat_r = [(seat_r[(k-1) % n]+2*seat_r[k]+seat_r[(k+1) % n])/4+.002 for k in range(n)]
    out = empty('headwear_tuque', 'headwear__tuque_red_1812')
    rings = []
    def ring(radii, y, centre=(cx, cz)):
        ids = []
        for k, (dx, dz) in enumerate(dirs):
            ids.append(len(out['positions_m']))
            out['positions_m'].append([centre[0]+radii[k]*dx, y, centre[1]+radii[k]*dz])
            out['uvs'].append([k/n, (y-seat)/.2]); out['weights'].append({'head': 1.})
        return ids
    # The cuff: a turned-up band, thicker than the crown, its lower edge tucked under.
    th = t['cuff_thickness']
    rings.append(ring([r-.003 for r in seat_r], seat+.004))
    rings.append(ring([r+th*.6 for r in seat_r], seat-.002))
    rings.append(ring([r+th for r in seat_r], seat+.006))
    rings.append(ring([r+th for r in seat_r], seat+t['cuff']-.004))
    rings.append(ring([r+th*.4 for r in seat_r], seat+t['cuff']))
    # The fitted crown: each ring at least the skull's own section plus the ease, up to
    # where the skull begins to round over.
    prev = seat_r
    rows = t['fitted_rows']
    crown_y = top-t['crown_below_top']
    for i in range(1, rows+1):
        y = seat+t['cuff']+(crown_y-seat-t['cuff'])*i/rows
        sec = section(y, t['ease'])
        radii = [max(s_, r*(1-.12*(i/rows)**2)) for s_, r in zip(sec, seat_r)]
        rings.append(ring(radii, y)); prev = radii
    # The soft top: a knitted tube whose axis rises over the crown, bends back and falls
    # behind the head, tapering; each ring square to the axis, so the bend does not shear.
    m = t['tail_rows']
    y0 = crown_y; mean = sum(prev)/n
    path = []
    for i in range(m+1):
        s_ = i/m; ang = math.pi*.75*s_**1.1
        R = t['tail_back']
        path.append((cx, y0+t['tail_rise']*math.sin(min(ang, math.pi/2))+(-t['tail_drop']*(s_-.55)/.45 if s_ > .55 else 0.),
                     cz-R*(1-math.cos(ang))))
    for i in range(1, m+1):
        s_ = i/m
        c = path[i]; pv = path[i-1]; nx_ = path[min(m, i+1)]
        T = [0., nx_[1]-pv[1], nx_[2]-pv[2]]; L_ = math.hypot(T[1], T[2]) or 1.; T = [0., T[1]/L_, T[2]/L_]
        N = [0., -T[2], T[1]]  # in the y-z plane, square to the axis; at the start it points forward
        rr = mean*(1-s_)**.9+t['tail_radius']*s_
        prev_r = [r*(1-s_)**.9+t['tail_radius']*s_ for r in prev]
        ids = []
        for k, (dx, dz) in enumerate(dirs):
            r = prev_r[k] if s_ < .2 else rr
            # dx along x, dz along the in-plane normal (forward at the start)
            ids.append(len(out['positions_m']))
            out['positions_m'].append([c[0]+r*dx, c[1]+r*dz*N[1], c[2]+r*dz*N[2]])
            out['uvs'].append([k/n, .5+.5*s_]); out['weights'].append({'head': 1.})
        rings.append(ids)
    for a_ring, b_ring in zip(rings, rings[1:]):
        for k in range(n):
            a, b, c, d = a_ring[k], a_ring[(k+1) % n], b_ring[(k+1) % n], b_ring[k]
            out['triangles'] += [[a, c, b], [a, d, c]]
    tip = len(out['positions_m']); last = path[-1]
    out['positions_m'].append([last[0], last[1]-.008, last[2]-.006]); out['uvs'].append([.5, 1.]); out['weights'].append({'head': 1.})
    for k in range(n):
        out['triangles'].append([rings[-1][k], rings[-1][(k+1) % n], tip])
    # Close the inside of the cuff upward to a lining over the hair.
    lining = ring([r*.5 for r in seat_r], top+.003)
    for k in range(n):
        a, b, c, d = rings[0][k], rings[0][(k+1) % n], lining[(k+1) % n], lining[k]
        out['triangles'] += [[a, b, c], [a, c, d]]
    lc = len(out['positions_m']); out['positions_m'].append([cx, top+.005, cz]); out['uvs'].append([.5, .5]); out['weights'].append({'head': 1.})
    for k in range(n):
        out['triangles'].append([lining[k], lining[(k+1) % n], lc])
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    out['receipt'] = dict(garment='red knitted cap, top falling to the back', seat_y_m=seat, cuff_m=t['cuff'],
                          tail_back_m=t['tail_back'], head_bone='head', separate_mesh=True, lift='rigid on the head bone')
    return out


def construct(body):
    need(TAILORING['shirt'] == L.TAILORING['shirt'] and TAILORING['trousers'] == L.TAILORING['trousers'],
         'the engage wears the 1835 labourer\'s shirt and trouser cut')
    before = digest(body)
    bones = {b['name']: b for b in body['skeleton']}
    height = max(p[1] for m in body['meshes'] for p in m['positions_m'])
    top = shirt(body, bones); legs = trousers(body, bones, height)
    wrap, ends = sash(body, bones, [top, legs])
    parts = [top, legs, wrap, ends, tuque(body, bones)]
    for m in parts:
        m.pop('_normals', None)
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_engage_1812_source_v1', license='CC0-1.0', units='m', up_axis='+Y',
                forward_axis='+Z', grade='reconstructed', assembly=ASSEMBLY, body_sha256=BODY_SHA256,
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts,
                materials=copy.deepcopy(MATERIALS), shoe_material=SHOE_MATERIAL, weave_material=WEAVE_MATERIAL,
                tailoring=copy.deepcopy(TAILORING),
                limitations=['Cut, ease, lengths and colours are reconstructed; no picture of a Chicago engage is known',
                             'Flat colours: the calico\'s print and the sash\'s woven pattern are not drawn',
                             'No cloth simulation: shells follow the body bones; the sash ends go with the left thigh',
                             'The shared closed foot loft stands for the moccasin; no seam, vamp or cuff',
                             'Cap rigid on the head bone; no pipe, knife or pack'])


def check_bundle(root, recipe, spec, bundle, body):
    """The provenance, colour and mesh checks every 1812 role of this family makes."""
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


def check_inputs(root, recipe, variant, body, spec, generator, recipe_path, assembly, tailoring, body_sha):
    need(spec.get('version') == 1 and spec.get('generator') == generator, 'unsupported role component generator')
    need(variant.get('recipe_path') == recipe_path and variant.get('component_assembly') == assembly,
         'role assembly is bound to its own recipe')
    need(recipe.get('scene_date') == '1812-08-14' and recipe.get('grade') == 'reconstructed',
         'role scene/appearance grade changed')
    need(spec.get('tailoring') == json.loads(json.dumps(tailoring)), 'recipe tailoring differs from the generator')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == body_sha == spec.get('body_sha256'), 'unreviewed role body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(spec.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'role components require the declared liberty')


def prepare_engage_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer for the 1812 engage; never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('engage_components', {})
    check_inputs(root, recipe, variant, body, spec, 'tools/human_engage_1812.py', RECIPE, ASSEMBLY, TAILORING, BODY_SHA256)
    bundle = construct(body)
    bundle['liberty'] = LIBERTY
    bundle['garments'] = [{'id': g['id'], 'material': g['material'], 'provenance': g['provenance']} for g in spec['garments']]
    check_bundle(root, recipe, spec, bundle, body)
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
