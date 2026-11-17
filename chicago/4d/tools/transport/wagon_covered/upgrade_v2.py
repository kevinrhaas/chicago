#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Covered wagons v2 (T-3558): each wagon's own cover on the photographic farm-box master.

Owner, 2026-10-21 (T-2980) and 2026-11-12 (T-3558): replace the older covered wagons with
better ones, each keeping its own finish, canvas ageing, seed and place so no two look like
clones. The v1 covered wagons stood their canvas on the plain original W01 running gear.
v2 stands each wagon's OWN v1 cover (its canvas sheet, sewn hems, five bows and laid-by
yoke, byte for byte) on the licensed photographic farm-box master that the 1812 and 1835
teams already drive, painted in the wagon's own seeded body and gear colours. The cover
also gains its own weathering, drawn from the wagon's own seed: grime at the hems and the
open ends, rain streaks between the bows and a sun-faded crown.

Writes `renderers/web/transport/covered-wagon/<variant>/covered-v2-cover.glb` for each
variant, and prints the placements.json model entries (`--entries`). `--verify` rebuilds in
memory and compares bytes. No network, Blender or new texture; the cover's textures are v1's.
"""
from pathlib import Path
import argparse, copy, hashlib, json, math, struct, sys

ROOT = Path(__file__).resolve().parents[3]
WEB = ROOT / 'renderers/web'
VARIANTS = ['covered_w01_western_blue', 'covered_w01_wolfpoint_oak']
COVER_MESHES = ['covered_original_canvas_sheet', 'covered_original_sewn_and_folded_hems',
                'covered_original_five_bows', 'covered_preserved_laid_by_yoke']
WEATHERED = {'covered_original_canvas_sheet', 'covered_original_sewn_and_folded_hems'}
FARM_BOX = 'transport/farm-box-master/farm-box-near.glb'
sha = lambda b: hashlib.sha256(b).hexdigest()


def glb(raw):
    n = struct.unpack_from('<I', raw, 12)[0]
    g = json.loads(raw[20:20 + n]); m = struct.unpack_from('<I', raw, 20 + n)[0]
    return g, raw[28 + n:28 + n + m]


def rng(seed):
    """Mulberry32, the project's seeded draw (data/transport/parked/covered-w01.json)."""
    state = [seed & 0xffffffff]
    def next_():
        state[0] = (state[0] + 0x6D2B79F5) & 0xffffffff
        t = state[0]
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xffffffff
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & 0xffffffff)) & 0xffffffff
        return ((t ^ (t >> 14)) & 0xffffffff) / 4294967296
    return next_


def weathering(seed):
    """Seeded large-scale canvas ageing as a vertex colour (multiplies v1's texture)."""
    r = rng(seed ^ 0x3558)
    streaks = [(-1.5 + 3.0 * r(), 0.05 + 0.08 * r(), 0.05 + 0.10 * r()) for _ in range(9)]
    blotches = [(-1.4 + 2.8 * r(), 1.7 + 0.8 * r(), 0.15 + 0.25 * r(), 0.03 + 0.05 * r()) for _ in range(6)]
    bleach = 0.03 + 0.05 * r(); grime = 0.10 + 0.12 * r(); ends = 0.06 + 0.08 * r(); base = 0.88 + 0.06 * r()
    def colour(x, y, z):
        h = min(1.0, max(0.0, (y - 1.45) / 1.15))            # 0 at the hem, 1 at the crown
        v = base + bleach * h ** 2
        v -= grime * math.exp(-(y - 1.45) / 0.22)
        v -= ends * math.exp(-(1.70 - abs(z)) / 0.18) if abs(z) < 1.70 else ends
        for zc, w, a in streaks:
            v -= a * (1 - h) ** 1.5 * math.exp(-((z - zc) / w) ** 2)
        for zc, yc, rad, a in blotches:
            v -= a * math.exp(-(((z - zc) ** 2 + (y - yc) ** 2) / rad ** 2))
        v = min(1.0, max(0.45, v))
        # Old duck yellows as it greys: a touch less blue where it is darkest.
        return [v, v * 0.995, v * (0.97 + 0.03 * v), 1.0]
    return colour


# The farm-box master's actual side-board tops (metres, every 0.1 m of z from -1.5 to +1.4),
# by a horizontal ray scan of farm-box-source.glb's body meshes at 5 mm steps. The artist's
# weathered boards are uneven: the +x top board falls from 1.495 to 1.29 towards the front
# and the -x side has lost its top board (1.305). A stake head at z +1.1 is left out.
SIDE_TOP = {+1: [1.495, 1.49, 1.48, 1.475, 1.47, 1.46, 1.455, 1.445, 1.44, 1.43, 1.425, 1.42, 1.41, 1.405, 1.395,
                 1.39, 1.38, 1.375, 1.37, 1.36, 1.355, 1.345, 1.34, 1.33, 1.325, 1.32, 1.3125, 1.305, 1.295, 1.29],
            -1: [1.305] * 27 + [1.29, 1.19, 1.12]}
TUCK, OUTSET, LOWEST, SKIRT_TOP = 0.02, 0.008, 1.29, 2.05


def side_top(side, z):
    z = min(1.4, max(-1.5, z)); t = (z + 1.5) / 0.1; i = min(int(t), 28); f = t - i
    row = SIDE_TOP[side]
    return max(LOWEST, row[i] + (row[i + 1] - row[i]) * f)


def fit(x, y, z):
    """Bring the cover's skirt (and the bows' feet) down onto this master's own side boards.

    v1's hem sat on W01's level 1.5 m sides. Below SKIRT_TOP the canvas eases down so its
    hem laps TUCK over the board top, and stands OUTSET proud of the board face. The crown
    is untouched."""
    side = 1 if x >= 0 else -1
    w = min(1.0, max(0.0, (SKIRT_TOP - y) / (SKIRT_TOP - 1.5))); w = w * w * (3 - 2 * w)
    drop = 1.5 - (side_top(side, z) - TUCK)
    return x + side * OUTSET * w, y - drop * w, z


def cover(variant, coat):
    raw = (WEB / f'transport/covered-wagon/{variant}/covered-w01.glb').read_bytes()
    g, b = glb(raw)
    out = {'asset': copy.deepcopy(g['asset']), 'scene': 0, 'nodes': [], 'meshes': [], 'materials': [],
           'textures': [], 'images': [], 'samplers': copy.deepcopy(g.get('samplers', [])),
           'accessors': [], 'bufferViews': [], 'buffers': []}
    out['asset']['generator'] = 'Chicago 4D covered wagon v2 cover (tools/transport/wagon_covered/upgrade_v2.py)'
    binary = bytearray()
    def view(data, target=None):
        binary.extend(b'\0' * ((-len(binary)) % 4))
        v = {'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}
        if target: v['target'] = target
        out['bufferViews'].append(v); binary.extend(data); return len(out['bufferViews']) - 1
    def copy_accessor(i):
        a = copy.deepcopy(g['accessors'][i]); v = g['bufferViews'][a['bufferView']]
        off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']] * {5126: 4, 5123: 2, 5125: 4}[a['componentType']]
        assert 'byteStride' not in v or v['byteStride'] == width
        a['bufferView'] = view(b[off:off + a['count'] * width], v.get('target')); a.pop('byteOffset', None)
        out['accessors'].append(a); return len(out['accessors']) - 1
    image_map, tex_map, mat_map = {}, {}, {}
    def copy_texture(ti):
        if ti in tex_map: return tex_map[ti]
        t = copy.deepcopy(g['textures'][ti]); si = t['source']
        if si not in image_map:
            im = copy.deepcopy(g['images'][si]); v = g['bufferViews'][im['bufferView']]
            im['bufferView'] = view(b[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])
            out['images'].append(im); image_map[si] = len(out['images']) - 1
        t['source'] = image_map[si]; out['textures'].append(t); tex_map[ti] = len(out['textures']) - 1
        return tex_map[ti]
    def copy_material(mi):
        if mi in mat_map: return mat_map[mi]
        m = copy.deepcopy(g['materials'][mi])
        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k.endswith('Texture') and isinstance(v, dict) and 'index' in v: v['index'] = copy_texture(v['index'])
                    else: walk(v)
        walk(m); out['materials'].append(m); mat_map[mi] = len(out['materials']) - 1
        return mat_map[mi]
    names = {m['name']: i for i, m in enumerate(g['meshes'])}
    parent = {c: i for i, n in enumerate(g['nodes']) for c in n.get('children', [])}
    node_of = {n['mesh']: i for i, n in enumerate(g['nodes']) if 'mesh' in n}
    paint = weathering(coat['seedUint32'])
    out['nodes'] = [{'name': 'vehicle_root', 'children': []}, {'name': 'vehicle_body', 'children': []}]
    out['nodes'][0]['children'].append(1)
    weathered_stats = {}
    for name in COVER_MESHES:
        mi = names[name]; mesh = copy.deepcopy(g['meshes'][mi]); prim = mesh['primitives'][0]
        frame = g['nodes'][parent[node_of[mi]]]['name']
        assert frame in ('vehicle_body', 'vehicle_root') and not any(k in g['nodes'][node_of[mi]] for k in ('translation', 'rotation', 'scale', 'matrix'))
        attrs = {k: copy_accessor(v) for k, v in prim['attributes'].items() if k != 'POSITION'}
        a = g['accessors'][prim['attributes']['POSITION']]; v = g['bufferViews'][a['bufferView']]
        off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        pts = struct.unpack_from('<' + 'f' * 3 * a['count'], b, off)
        if frame == 'vehicle_body':
            moved = [fit(*pts[3 * i:3 * i + 3]) for i in range(a['count'])]
            packed = struct.pack('<' + 'f' * 3 * len(moved), *(c for p in moved for c in p))
            back = struct.unpack('<' + 'f' * 3 * len(moved), packed)
            out['accessors'].append({'bufferView': view(packed, 34962), 'componentType': 5126, 'count': len(moved), 'type': 'VEC3',
                                     'min': [min(back[k::3]) for k in range(3)], 'max': [max(back[k::3]) for k in range(3)]})
            attrs['POSITION'] = len(out['accessors']) - 1
        else:
            attrs['POSITION'] = copy_accessor(prim['attributes']['POSITION'])
        attrs = {k: attrs[k] for k in prim['attributes']}
        if name in WEATHERED:
            cols = [paint(*pts[3 * i:3 * i + 3]) for i in range(a['count'])]
            data = struct.pack('<' + 'f' * 4 * len(cols), *(c for col in cols for c in col))
            out['accessors'].append({'bufferView': view(data, 34962), 'componentType': 5126, 'count': len(cols), 'type': 'VEC4'})
            attrs['COLOR_0'] = len(out['accessors']) - 1
            vals = [c[0] for c in cols]
            weathered_stats[name] = {'min': round(min(vals), 4), 'mean': round(sum(vals) / len(vals), 4), 'max': round(max(vals), 4)}
        prim['attributes'] = attrs; prim['material'] = copy_material(prim['material'])
        out['meshes'].append(mesh)
        out['nodes'].append({'name': name, 'mesh': len(out['meshes']) - 1})
        out['nodes'][0 if frame == 'vehicle_root' else 1]['children'].append(len(out['nodes']) - 1)
    out['scenes'] = [{'nodes': [0]}]
    binary.extend(b'\0' * ((-len(binary)) % 4))
    out['buffers'] = [{'byteLength': len(binary)}]
    out['extras'] = {'asset_id': f'{variant}_v2_cover', 'ticket': 'T-3558', 'grade': 'reconstructed',
                     'cover_from_v1_sha256': sha(raw), 'seedUint32': coat['seedUint32'],
                     'weathering': {'kind': 'seeded vertex-colour ageing of the canvas and hems (grime at hems and open ends, rain streaks, blotches, sun-faded crown)', 'value_range': weathered_stats},
                     'stands_on': FARM_BOX}
    if not out['samplers']: out.pop('samplers')
    j = json.dumps(out, separators=(',', ':')).encode(); j += b' ' * ((-len(j)) % 4)
    return struct.pack('<III', 0x46546c67, 2, 28 + len(j) + len(binary)) + struct.pack('<II', len(j), 0x4e4f534a) + j + struct.pack('<II', len(binary), 0x004e4942) + bytes(binary)


def linear(hexvalue):
    v = int(hexvalue.lstrip('#'), 16); o = []
    for shift in (16, 8, 0):
        c = ((v >> shift) & 255) / 255; o.append(c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4)
    return o


# Mean linear albedo of the farm-box master's weathered-board pixels (luma 0.06-0.6, so the
# black ironwork and empty atlas are left out), measured from farm-box-near.glb's WebP maps.
# Recorded rather than decoded here: lossy WebP decoders may differ in the last bits.
BOARD_ALBEDO = {'CartBase': [0.1997, 0.1758, 0.1508], 'CartDetails': [0.2164, 0.1821, 0.1526]}
BODY_MESHES = ['CartBody_CartBase_0', 'CartBody_CartDetails_0']


def paint(coat):
    """Seeded body/gear paint as colour multipliers over the photographic board maps.

    Each factor brings the boards' mean to the wagon's own seeded paint (its v1 colour
    times its age scalar) while the grain, knots, wear and ironwork of the photographed
    timber still modulate it. Bounded at 3 so ironwork never lights up.
    """
    def factors(hexvalue, scalar):
        target = [c * scalar for c in linear(hexvalue)]
        return {m: [round(min(3.0, t / r), 4) for t, r in zip(target, ref)] for m, ref in BOARD_ALBEDO.items()}
    return {'body_meshes': BODY_MESHES,
            'body': factors(coat['baseSrgb']['body'], coat['ageScalar']),
            'gear': factors(coat['baseSrgb']['gear'], coat['gearScalar'])}


def entries():
    data = json.loads((ROOT / 'data/transport/parked/covered-w01.json').read_text())
    by_variant = {}
    for v in data['variants']:
        key = 'covered_w01_' + ('western_blue' if 'western' in v['id'] else 'wolfpoint_oak')
        by_variant[key] = v['coat']
    return by_variant


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--verify', action='store_true'); ap.add_argument('--entries', action='store_true')
    a = ap.parse_args()
    coats = entries(); report = {}
    for variant in VARIANTS:
        raw = cover(variant, coats[variant]); path = WEB / f'transport/covered-wagon/{variant}/covered-v2-cover.glb'
        if a.verify:
            assert path.read_bytes() == raw, f'{variant}: covered-v2-cover.glb is stale; run upgrade_v2.py'
        else:
            path.write_bytes(raw)
        report[variant] = {'file': FARM_BOX, 'support_file': str(path.relative_to(WEB)),
                           'support_sha256': sha(raw), 'support_bytes': len(raw), 'paint': paint(coats[variant])}
    print(json.dumps(report, indent=1))
    return report


if __name__ == '__main__':
    main()
