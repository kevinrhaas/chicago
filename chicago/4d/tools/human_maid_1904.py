# SPDX-License-Identifier: GPL-3.0-or-later
"""A 1904 house maid's dress on the shared portable female rig (T-3448).

First worn by Mary Reynolds, house maid in the Glessner household at 1800 Prairie Avenue
in the 1900 census. The pieces, read from the period pictures in the recipe
(data/humans/recipes/maid_1904.json):

  dress          a black work dress: a long-sleeved bodice, a little full in front and at the
                 upper sleeve, with a high neck, over a full black skirt to the floor (the
                 maid at the front door, Kelley, 1904; the maid seen from behind, Graves, 1905)
  collar, cuffs  white: a narrow band round the top of the high neck and at each wrist
                 (the 1904 maid's white collar)
  apron          white: a broad skirt reaching nearly to the hem and round the sides, a bib
                 over the bodice front and two wide straps over the shoulders to the waist
                 behind (the 1904 maid; the bib aprons of the 1903 Wasson stereographs), and a
                 bow of its ties at the back of the waist (the 1905 maid seen from behind)
  cap            a small white frilled cap pinned on the crown of the drawn-up hair (the 1904
                 maid; the 1903 Wasson maid). A separate mesh rigidly on the head bone
                 (material `headwear__maid_cap_white`).

Generated geometry is CC0-1.0. The bodice, skirt, bib and straps are the dress components of
T-3423 (tools/human_dress_components.py), re-cut and re-coloured here; amounts and every colour
are reconstructed (the pictures are monochrome); liberty L-human-modular-dress-1789 with its
T-3448 supplement. The source anatomy is never changed.

Pure Python (no Blender); the canonical builder tools/human_teamster_blend.py calls
prepare_maid_assembly() and makes the four LODs.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path

from human_dress_components import (need, digest, empty, bodice, blouse, skirt as gathered_skirt, bib, straps,
                                    collar_band, skin)
from human_period_wardrobe import finish_edges

BODY_SHA256 = '3060ee86957ff7c2d70c89e70fe95ff3bc2294a0d7f6a5716b5a2f3f8dd84c72'
ASSEMBLY = 'maid_1904_v1'
RECIPE = 'data/humans/recipes/maid_1904.json'
LIBERTY = 'L-human-modular-dress-1789'

# Every dimension of the outfit, in metres; the recipe repeats them for review and the
# builder refuses a recipe that disagrees. All are reconstructed choices.
TAILORING = dict(
    bodice=dict(ease=.016, collar=.026, waist_below_spine02=.018, pouch=.012, sleeve=.010),
    collar=dict(below=.012, lift=.0022),
    cuffs=dict(length=.055, lift=.0022),
    skirt=dict(hem_y=.040, ease=.015, segments=96, rows=18),
    apron=dict(columns_each_side=17, last_row_from_hem=2, offset=.008),
    bib=dict(top=.205, half_width=[.112, .094], offset=.007),
    straps=dict(centre_x=.080, width=.034, offset=.0055, steps=40, frill=.044, frill_waves=9),
    bow=dict(loop_length=.075, loop_height=.035, tail_length=.24, tail_width=.045, standoff=.012),
    cap=dict(radius=.052, frill=.020, frill_waves=14, forward_of_crown=.03, lift=.004),
)

MATERIALS = {
    'garment_upper__maid_dress_black': {'base_color_linear': [.022, .022, .026, 1], 'roughness': .88},
    'garment_lower__maid_skirt_black': {'base_color_linear': [.022, .022, .026, 1], 'roughness': .9},
    'garment_outer__maid_apron_white': {'base_color_linear': [.74, .74, .71, 1], 'roughness': .86},
    'headwear__maid_cap_white': {'base_color_linear': [.76, .76, .73, 1], 'roughness': .84},
    'footwear__maid_shoes_black': {'base_color_linear': [.014, .013, .012, 1], 'roughness': .45},
}
SHOE_MATERIAL = 'footwear__maid_shoes_black'
WEAVE_MATERIAL = 'garment_upper__maid_dress_black'


def _two_sided(out, eps=.0006):
    """A thin piece seen from both sides: each face once as wound, and once more on its own
    copy of the vertices set `eps` behind it, wound the other way. Faces that share vertices
    with their reverse cancel each other's normals and shade as broken shards."""
    seen, faces = set(), []
    for f in out['triangles']:
        key = frozenset(f)
        if key not in seen:
            seen.add(key); faces.append(f)
    P = out['positions_m']
    normal = [[0., 0., 0.] for _ in P]
    for a, b, c in faces:
        u = [P[b][i]-P[a][i] for i in range(3)]; v = [P[c][i]-P[a][i] for i in range(3)]
        n = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        for i in (a, b, c):
            normal[i] = [normal[i][k]+n[k] for k in range(3)]
    count = len(P)
    for i in range(count):
        m = math.sqrt(sum(x*x for x in normal[i])) or 1.
        P.append([P[i][k]-eps*normal[i][k]/m for k in range(3)])
        out['uvs'].append(list(out['uvs'][i])); out['weights'].append(dict(out['weights'][i]))
    out['triangles'] = faces+[[a+count, c+count, b+count] for a, b, c in faces]
    out['corner_uvs'] = [[out['uvs'][i] for i in f] for f in out['triangles']]
    return out


def cuffs(upper, bones):
    """White cuffs: the bodice's own triangles over the last `length` of each sleeve, copied
    a little out from the forearm's axis, skinned as the sleeve is there."""
    t = TAILORING['cuffs']
    P = upper['positions_m']
    out = empty('white_cuffs', 'garment_outer__maid_apron_white')
    index = {}
    for f, corner in zip(upper['triangles'], upper['corner_uvs']):
        xs = [abs(P[i][0]) for i in f]
        side = 'l' if P[f[0]][0] > 0 else 'r'
        end = abs(bones[f'hand_{side}']['head_m'][0])
        if min(xs) < end-t['length'] or max(xs) > end+.01:
            continue
        ax = bones[f'lowerarm_{side}']['head_m']
        ids = []
        for i in f:
            if i not in index:
                p = P[i]; dy, dz = p[1]-ax[1], p[2]-ax[2]; r = math.hypot(dy, dz)
                need(r > .005, 'cuff point on the forearm axis')
                index[i] = len(out['positions_m'])
                out['positions_m'].append([p[0], p[1]+t['lift']*dy/r, p[2]+t['lift']*dz/r])
                out['uvs'].append(list(upper['uvs'][i])); out['weights'].append(dict(upper['weights'][i]))
            ids.append(index[i])
        out['triangles'].append(ids); out['corner_uvs'].append([list(c) for c in corner])
    need(bool(out['triangles']), 'no sleeve end for the cuffs')
    out = finish_edges(out, .0012)
    out['receipt'] = dict(garment='white cuffs', length_m=t['length'], lift_m=t['lift'])
    return out


def strap_frills(strap, bones):
    """The broad frills along the outer edge of each apron strap, standing out over the
    shoulder like a small cape and narrowing to nothing at the bib and at the waist behind,
    fluted along their length; double-sided, skinned as the strap edge they hang from."""
    t = TAILORING['straps']
    steps = t['steps']
    P = strap['positions_m']; W = strap['weights']
    need(len(P) >= 2*2*steps and all(math.dist(P[2*k], P[2*k+1]) < .1 for k in range(steps)), 'unexpected apron strap layout')
    shoulder = bones['clavicle_l']['head_m'][1]
    out = empty('apron_strap_frills', 'garment_outer__maid_apron_white')
    for side in range(2):
        base = side*2*steps
        sign = 1 if P[base][0] > 0 else -1
        ids = []
        for k in range(steps):
            q = P[base+2*k+1]
            # Fullest over the shoulder, fading down the front and the back.
            g = max(0., 1-abs(q[1]-shoulder)/.24)
            g = g*g*(3-2*g)
            flute = .5*(1+math.cos(t['frill_waves']*2*math.pi*k/(steps-1)))
            w = t['frill']*g*(.8+.2*flute)
            # Out from the strap's outer edge, standing off the body: half across the strap's
            # own surface, half along its outward normal, so the frill stands up and out over
            # the shoulder instead of lying in the bodice.
            p_in = P[base+2*k]
            nxt, prv = P[base+2*min(steps-1, k+1)+1], P[base+2*max(0, k-1)+1]
            along = [nxt[i]-prv[i] for i in range(3)]
            across = [q[i]-p_in[i] for i in range(3)]
            nrm = [along[1]*across[2]-along[2]*across[1], along[2]*across[0]-along[0]*across[2], along[0]*across[1]-along[1]*across[0]]
            centre = [0., q[1], bones['spine_03']['head_m'][2]]
            if sum(nrm[i]*(q[i]-centre[i]) for i in range(3)) < 0:
                nrm = [-x for x in nrm]
            la, ln = math.sqrt(sum(x*x for x in across)) or 1., math.sqrt(sum(x*x for x in nrm)) or 1.
            d = [.6*across[i]/la+.8*nrm[i]/ln for i in range(3)]
            for e, f in enumerate((0., w)):
                ids.append(len(out['positions_m']))
                out['positions_m'].append([q[i]+f*d[i] for i in range(3)]); out['uvs'].append([e, k/(steps-1)])
                out['weights'].append(dict(W[base+2*k+1]))
        for k in range(steps-1):
            a = ids[2*k]; b = ids[2*k+1]; c = ids[2*k+3]; d = ids[2*k+2]
            out['triangles'] += [[a, c, b], [a, d, c], [a, b, c], [a, c, d]]
    out['triangles'] = [f for f in out['triangles'] if len({tuple(out['positions_m'][i]) for i in f}) == 3]
    out = _two_sided(out)
    out['receipt'] = dict(garment='strap frills', width_m=t['frill'], double_sided=True)
    return out


def apron_skirt(dress, rows, segments):
    """The apron's skirt: a broad panel following the dress skirt's own surface round the
    front and well onto the sides, from the waist to `last_row_from_hem` rows above the hem."""
    t = TAILORING['apron']
    out = empty('maid_apron_skirt', 'garment_outer__maid_apron_white')
    columns = list(range(-t['columns_each_side'], t['columns_each_side']+1))
    last = rows-t['last_row_from_hem']
    for row in range(last):
        for col in columns:
            k = col % segments; base = dress['positions_m'][row*segments+k]
            r = math.hypot(base[0], base[2]); off = t['offset']
            out['positions_m'].append([base[0]*(1+off/r), base[1]+.001, base[2]*(1+off/r)])
            out['uvs'].append([(col-columns[0])/(columns[-1]-columns[0]), row/(last-1)])
            out['weights'].append(dict(dress['weights'][row*segments+k]))
    width = len(columns)
    for row in range(last-1):
        for k in range(width-1):
            a = row*width+k; b = a+1; c = a+width+1; d = a+width
            for face in ([a, c, b], [a, d, c]):
                out['triangles'].append(face); out['corner_uvs'].append([out['uvs'][i] for i in face])
    out = finish_edges(out, .0015)
    out['receipt'] = dict(garment='apron skirt', columns=width, of_segments=segments, rows=last)
    return out


def bow(dress, bones, waist, segments):
    """The apron ties' bow at the back of the waist: two flattened loops and two tails
    falling over the skirt behind, stood off the skirt's back, skinned as the skirt there."""
    t = TAILORING['bow']
    P = dress['positions_m']; W = dress['weights']
    back = segments//2   # the skirt's ring index pointing straight back (-z)
    top = P[back]        # first ring, at the waist
    y0 = waist-.01
    z0 = top[2]-t['standoff']
    w0 = dict(W[back])
    out = empty('apron_bow', 'garment_outer__maid_apron_white')
    def strip(points, width_at):
        base = len(out['positions_m'])
        n = len(points)
        for i, (x, y, z) in enumerate(points):
            hw = width_at(i/(n-1))
            for e in (-1, 1):
                out['positions_m'].append([x, y+e*hw, z]); out['uvs'].append([(e+1)/2, i/(n-1)]); out['weights'].append(dict(w0))
        for i in range(n-1):
            a = base+2*i; b = a+1; c = a+3; d = a+2
            out['triangles'] += [[a, c, b], [a, d, c], [a, b, c], [a, c, d]]
    for side in (1, -1):
        loop = [(side*t['loop_length']*math.sin(math.pi*s)*.9+side*.004, y0+.004*math.sin(2*math.pi*s),
                 z0-.012*math.sin(math.pi*s)) for s in [i/12 for i in range(13)]]
        strip(loop, lambda s: t['loop_height']/2*(.45+.55*math.sin(math.pi*s)))
    for side in (1, -1):
        tail = []
        for i in range(10):
            s = i/9; y = y0-.01-t['tail_length']*s
            # Follow the skirt's back down so the tail lies on it.
            row_y = min(range(len(P)//segments), key=lambda r: abs(P[r*segments+back][1]-y))
            zb = P[row_y*segments+back][2]-.006
            tail.append((side*(.012+.02*s), y, min(z0, zb)))
        base = len(out['positions_m'])
        for i, (x, y, z) in enumerate(tail):
            hw = t['tail_width']/2*(.6+.4*i/9)
            for e in (-1, 1):
                out['positions_m'].append([x+e*hw, y, z]); out['uvs'].append([(e+1)/2, i/9]); out['weights'].append(dict(w0))
        for i in range(9):
            a = base+2*i; b = a+1; c = a+3; d = a+2
            out['triangles'] += [[a, c, b], [a, d, c], [a, b, c], [a, c, d]]
    out = _two_sided(out)
    out['receipt'] = dict(garment='apron bow at the back', y_m=y0, double_sided=True, skinning='skirt back at the waist')
    return out


def cap(hair, lod=0):
    """A small white frilled cap pinned on the crown: a shallow dome laid over the hair's
    own top a little forward of the crown, ringed by a fluted frill standing up and out.
    Rigid on the head bone, a separate mesh."""
    t = TAILORING['cap']
    Q = hair['positions_m']
    top = max(Q, key=lambda p: p[1])
    cx, cz = top[0], top[2]+t['forward_of_crown']
    def hair_y(x, z, reach=.008):
        near = [p[1] for p in Q if abs(p[0]-x) < reach and abs(p[2]-z) < reach]
        return max(near) if near else None
    rings, n = (5, (84, 56, 36, 24)[lod])
    out = empty('headwear_maid_cap', 'headwear__maid_cap_white')
    grid = []
    for r in range(rings+1):
        f = r/rings; row = []
        for k in range(n if r else 1):
            a = 2*math.pi*k/n
            x = cx+t['radius']*f*math.sin(a); z = cz+t['radius']*f*math.cos(a)
            y = hair_y(x, z)
            if y is None:
                y = hair_y(x, z, .03) or top[1]
            row.append(len(out['positions_m']))
            out['positions_m'].append([x, y+t['lift'], z]); out['uvs'].append([.5+.5*f*math.sin(a), .5+.5*f*math.cos(a)])
            out['weights'].append({'head': 1.})
        grid.append(row)
    # The hair's top is uneven strand by strand; a starched cap is not. Each ring's heights
    # are averaged round the ring, never sinking more than 2 mm into the hair (pinned into it).
    Pm = out['positions_m']
    for row in grid[1:]:
        ys = [Pm[i][1] for i in row]
        m = len(ys)
        env = list(ys)
        for _ in range(4):
            env = [(env[k-1]+2*env[k]+env[(k+1) % m])/4 for k in range(m)]
        for i, y, y0 in zip(row, env, ys):
            Pm[i][1] = max(y, y0-.002)
    for k in range(n):
        out['triangles'].append([grid[0][0], grid[1][(k+1) % n], grid[1][k]])
    for r in range(1, rings):
        for k in range(n):
            a, b, c, d = grid[r][k], grid[r][(k+1) % n], grid[r+1][(k+1) % n], grid[r+1][k]
            out['triangles'] += [[a, c, b], [a, d, c]]
    # The frill: a fluted band up and out from the dome's rim, double-sided.
    rim = grid[-1]; frill = []
    waves = t['frill_waves']
    for k in range(n):
        a = 2*math.pi*k/n
        x0, y0, z0 = out['positions_m'][rim[k]]
        flute = .5*(1+math.cos(waves*a))
        # Fluted in and out round its edge; an even height, so the rim reads as a frill, not points.
        dr = t['frill']*(.8+.2*flute); dy = t['frill']*.5
        frill.append(len(out['positions_m']))
        out['positions_m'].append([x0+dr*math.sin(a), y0+dy, z0+dr*math.cos(a)]); out['uvs'].append([k/n, 1.]); out['weights'].append({'head': 1.})
    for k in range(n):
        a, b, c, d = rim[k], rim[(k+1) % n], frill[(k+1) % n], frill[k]
        out['triangles'] += [[a, c, b], [a, d, c], [a, b, c], [a, c, d]]
    out = _two_sided(out)
    out['receipt'] = dict(garment='white frilled cap', centre_m=[cx, top[1], cz], radius_m=t['radius'], frill_m=t['frill'],
                          head_bone='head', separate_mesh=True, double_sided=True)
    return out


def construct(body, hair):
    before = digest(body)
    bones = {b['name']: b for b in body['skeleton']}
    t = TAILORING
    spine = bones['spine_02']['head_m'][1]
    waist = spine-t['bodice']['waist_below_spine02']
    upper = bodice(body, bones, waist, ease=t['bodice']['ease'], collar=t['bodice']['collar'])
    upper = blouse(upper, bones, waist, pouch=t['bodice']['pouch'], sleeve=t['bodice']['sleeve'])
    upper['name'] = 'maid_bodice'; upper['material'] = 'garment_upper__maid_dress_black'
    s = t['skirt']
    lower, core = gathered_skirt(body, bones, spine, upper, segments=s['segments'], rows=s['rows'], ease=s['ease'], hem=s['hem_y'])
    lower['name'] = 'maid_skirt'; lower['material'] = 'garment_lower__maid_skirt_black'
    collar = collar_band(upper, bones, below=t['collar']['below'], lift=t['collar']['lift'])
    collar['name'] = 'white_collar'; collar['material'] = 'garment_outer__maid_apron_white'
    b = t['bib']; st = t['straps']
    strap_mesh = straps(upper, bones, waist, top=b['top'], centre_x=st['centre_x'], width=st['width'], offset=st['offset'], steps=st['steps'])
    parts = [upper, lower, apron_skirt(lower, s['rows'], s['segments']),
             bib(upper, bones, waist, top=b['top'], half_width=tuple(b['half_width']), offset=b['offset']),
             strap_mesh,
             collar, cuffs(upper, bones), strap_frills(strap_mesh, bones), bow(lower, bones, spine, s['segments']), cap(hair)]
    for m in parts:
        if m['material'] == 'garment_outer__plain_apron':
            m['material'] = 'garment_outer__maid_apron_white'
    need(before == digest(body), 'garment constructor mutated source anatomy, rig or UVs')
    return dict(format='chicago4d_maid_1904_source_v1', license='CC0-1.0', units='m', up_axis='+Y',
                forward_axis='+Z', grade='reconstructed', assembly=ASSEMBLY, body_sha256=BODY_SHA256,
                body_semantic_sha256=before, source_body_unchanged=True, meshes=parts,
                materials=copy.deepcopy(MATERIALS), shoe_material=SHOE_MATERIAL, weave_material=WEAVE_MATERIAL,
                tailoring=copy.deepcopy(TAILORING),
                limitations=['Cut, ease, lengths, folds and colours are reconstructed; the pictures are monochrome',
                             'No cloth simulation: skirt and apron share the leg-following skirt weights (T-3423)',
                             'Cap rigid on the head bone, laid over the fitted bun hair'])


def prepare_maid_assembly(root, recipe, variant, body):
    """The canonical builder's source consumer for T-3448; never a world switch."""
    root = Path(root).resolve()
    spec = recipe.get('maid_components', {})
    need(spec.get('version') == 1 and spec.get('generator') == 'tools/human_maid_1904.py',
         'unsupported maid component generator')
    need(variant.get('recipe_path') == RECIPE and variant.get('component_assembly') == ASSEMBLY,
         'maid assembly is bound to its own recipe')
    need(recipe.get('scene_date') == '1904-07-01' and recipe.get('grade') == 'reconstructed',
         'maid scene/appearance grade changed')
    need(spec.get('tailoring') == TAILORING, 'recipe tailoring differs from the generator')
    relative = Path(variant['body_input'])
    need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe body path')
    source = (root/relative).resolve()
    need(source.is_relative_to(root) and source.is_file(), 'body source absent/outside checkout')
    raw = source.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256 == spec.get('body_sha256'), 'unreviewed maid body source')
    need(json.loads(raw) == body and body.get('license') == 'CC0-1.0', 'changed anatomy or source rights')
    need(spec.get('liberty') == LIBERTY and ('### '+LIBERTY+' ') in (root/'docs/LIBERTIES.md').read_text(),
         'maid components require the declared liberty')
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
    need(recipe['hair_component'].get('fitter') == 'mhclo_proxy', 'the cap is laid over the fitted bun hair')
    from human_hair_proxy import fit
    hair = fit(body, recipe['hair_component'], root)[0]
    bundle = construct(body, hair)
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
    p = argparse.ArgumentParser(); p.add_argument('--body', type=Path, required=True); p.add_argument('--recipe', type=Path, required=True)
    a = p.parse_args(); raw = a.body.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == BODY_SHA256, 'unreviewed body source')
    from human_hair_proxy import fit
    body = json.loads(raw)
    hair = fit(body, json.loads(a.recipe.read_text())['hair_component'], Path(__file__).resolve().parent.parent)[0]
    data = construct(body, hair)
    print(json.dumps({'meshes': [{'name': m['name'], 'material': m['material'], 'vertices': len(m['positions_m']),
                                  'triangles': len(m['triangles']), 'receipt': m.get('receipt')} for m in data['meshes']]}, indent=1, default=str))
