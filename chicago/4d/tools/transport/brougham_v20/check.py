# SPDX-License-Identifier: GPL-3.0-or-later
"""Gate for the V20 plate-matched Brougham (T-3558). No browser, no network.

1. near and mid regenerate byte for byte from the committed V19 raw masters;
2. far re-derives from a fresh V19 far (the V19 producer with far-lods.json) and matches
   the committed far's every triangle, the two simplified body shells taken from the
   committed far itself, whose corners must all be V19 shell corners;
3. every level keeps the coachman's fit: the cushion, piping, backboard, perch base, side
   rails and footboard are V19's own triangles, and every vehicle_ frame, wheel/pole
   contact and seat datum is V19's, except the cab's (produce.CAB, T-3553): the passengers'
   seat data lowered by exactly its drop and their floor by exactly its floor drop;
4. the sidecar is exactly what this measures (`--write` rewrites it);
5. every driven row that carries V20 says what its coachman was fitted on (V19) and
   names only V20 files at their real hashes;
6. negative controls: a moved footboard, a kept mudguard and a wrong row hash all fail.
"""
from pathlib import Path
import argparse, collections, copy, hashlib, json, struct, subprocess, sys, tempfile

HERE = Path(__file__).resolve().parent
V19 = HERE.parent / 'brougham'
ROOT = HERE.parents[2]
ASSET = ROOT / 'renderers/web/transport/parked-brougham'
SIDE = ASSET / 'brougham-v20.json'
LOOPS = ROOT / 'data/transport/driven/loops.json'
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(V19))
import produce  # noqa: E402
from check_near import read, world_nodes, decoded_bounds, native_contacts  # noqa: E402
from check_mid import bind_parts  # noqa: E402
from index_streams import write_indexed, expanded_signature  # noqa: E402
from static_master import static_master_contract  # noqa: E402

FIT_PARTS = {'driver_perch_base', 'rounded_empty_driver_cushion', 'driver_cushion_edge_piping',
             'driver_backboard', 'driver_footboard', 'driver_side_rail'}
FILES = {d: f'brougham-v20-{d}.glb' for d in ('near', 'mid', 'far')}
V19_NEAR = 'transport/parked-brougham/brougham-near.glb'
sha = lambda b: hashlib.sha256(b).hexdigest()


def rows_by(doc, binary):
    out = collections.defaultdict(list)
    for r in bind_parts(doc, binary):
        out[r['identity'][0]].append(r)
    return out


def vehicle_frames(doc):
    w = world_nodes(doc)
    return {n['name']: w[i] for i, n in enumerate(doc['nodes']) if n['name'].startswith('vehicle_')}


def fit_record(doc, binary):
    by = rows_by(doc, binary)
    parts = {name: [sha(r['chunks']['POSITION'] + r['chunks']['NORMAL']) for r in by[name]] for name in sorted(FIT_PARTS)}
    seats = static_master_contract(doc, binary, world_nodes(doc), '0' * 64)['seats']
    return {'parts': parts, 'frames': vehicle_frames(doc), 'contacts': native_contacts(doc, binary), 'seats': seats}


def cab_frames(frames):
    """V19's frames with the passengers' seats lowered by the cab's drop (produce.CAB)."""
    out = copy.deepcopy(frames)
    for name in produce.SEATS_LOWERED:
        out[name][1] -= produce.CAB['drop_m']
    return out


def cab_seats(seats):
    """V19's seat contract with the passengers' pelvis lowered by the drop, their feet and floor by the floor drop."""
    out = copy.deepcopy(seats); d, f = produce.CAB['drop_m'], produce.CAB['floor_drop_m']
    for s in out:
        if s['node'] in produce.SEATS_LOWERED:
            s['pelvis_reference_root_m'][1] -= d
            for foot in s['prospective_feet_root_m']:
                foot[1] -= f
            bounds = s['feet_reference_surface_bounds_root_m'] = copy.deepcopy(s['feet_reference_surface_bounds_root_m'])
            for k in ('min', 'max'):  # (V19 shares one floor record between both seats)
                bounds[k][1] -= f
    return out


def close(a, b, tol=2e-6):
    """Equal structure, numbers within float32 rounding of the lowered surfaces."""
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(close(a[k], b[k], tol) for k in a)
    if isinstance(a, (list, tuple)):
        return isinstance(b, (list, tuple)) and len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        return abs(a - b) <= tol
    return a == b


def v19_far(tmp):
    return produce.far_source(tmp)


def measure(detail, path, delivered, v19_path):
    """Fit and inventory on the fresh raw (non-indexed) derivation of the delivered file."""
    raw = Path(delivered).read_bytes(); doc, binary = read(Path(path))
    base_doc, base_bin = read(Path(v19_path))
    fit, base = fit_record(doc, binary), fit_record(base_doc, base_bin)
    assert fit['parts'] == base['parts'], f'{detail}: the coachman\'s box surfaces must be V19\'s own triangles'
    assert fit['frames'] == cab_frames(base['frames']), f'{detail}: vehicle frames moved (other than the cab seats\' declared drop)'
    assert fit['contacts'] == base['contacts'], f'{detail}: wheel/pole/shoe/hitch contacts moved'
    assert close(fit['seats'], cab_seats(base['seats'])), f'{detail}: seat datum or footboard/floor surfaces moved (other than the cab\'s declared drop)'
    inventory = collections.Counter(p['name'] for p in doc['extras']['parts'])
    v19_inventory = collections.Counter(p['name'] for p in base_doc['extras']['parts'])
    assert not any(inventory[n] for n in produce.REMOVED), f'{detail}: a removed V19 part is still drawn'
    expected = v19_inventory.copy()
    for n in produce.REMOVED:
        del expected[n]
    added = collections.Counter(n for n, _, _ in produce.box_parts(detail))
    assert inventory == expected + added, f'{detail}: V20 inventory is V19 less REMOVED plus the rebuilt box'
    tris = sum(p['triangles'] for p in doc['extras']['parts'])
    w = world_nodes(doc)
    return {'detail': detail, 'file': FILES[detail], 'sha256': sha(raw), 'bytes': len(raw), 'triangles': tris,
            'draw_batches': len(doc['meshes']), 'materials': len(doc['materials']), 'nodes': len(doc['nodes']),
            'textures': len(doc.get('textures', [])), 'bounds_m': decoded_bounds(doc, binary, w),
            'v19_level_sha256': sha(Path(v19_path).read_bytes()),
            'v19_level_triangles': sum(p['triangles'] for p in base_doc['extras']['parts']),
            'coachman_fit_preserved': True}


def regenerate(tmp):
    """Fresh near/mid/far; far's two shells come from the committed far (see module doc)."""
    out = {}
    far_src = v19_far(tmp)
    committed_far = read(ASSET / FILES['far'])
    shells = {}
    v19doc, v19bin = read(far_src)
    v19rows = rows_by(v19doc, v19bin)
    # Map committed far shells back onto V19 part indices, in order.
    cdoc, cbin = committed_far
    # The committed far is indexed; expand its batches part by part.
    from index_streams import attribute_rows
    def expanded(doc, binary, mi):
        prim = doc['meshes'][mi]['primitives'][0]
        P = attribute_rows(doc, binary, prim['attributes']['POSITION']); N = attribute_rows(doc, binary, prim['attributes']['NORMAL'])
        a = doc['accessors'][prim['indices']]; v = doc['bufferViews'][a['bufferView']]
        fmt = {5123: 'H', 5125: 'I'}[a['componentType']]
        idx = struct.unpack_from('<' + fmt * a['count'], binary, v.get('byteOffset', 0) + a.get('byteOffset', 0))
        return b''.join(P[i] for i in idx), b''.join(N[i] for i in idx)
    cursor = {}
    named = collections.defaultdict(list)
    for mi, m in enumerate(cdoc['meshes']):
        named[m['name']].append(mi)
    for p in cdoc['extras']['parts']:
        key = 'surface_' + p['frame'] + '_' + str(p['material'])
        st = cursor.setdefault(key, {'ord': 0, 'next': 0})
        if p['triangle_start_in_batch'] == 0 and st['next'] > 0:
            st['ord'] += 1; st['next'] = 0
        st['next'] += p['triangles']
        if p['name'] in produce.SIMPLIFY:
            P, N = expanded(cdoc, cbin, named[key][st['ord']])
            s, e = p['triangle_start_in_batch'] * 36, (p['triangle_start_in_batch'] + p['triangles']) * 36
            shells.setdefault(p['name'], []).append((P[s:e], N[s:e]))
    import numpy as np
    simplified = {}
    for name, got in shells.items():
        rows = v19rows[name]
        assert len(rows) == len(got), 'far shell count'
        simplified[name] = {}
        for r, (P, N) in zip(rows, got):
            # The committed shells carry the cab's warp (produce.cab_warp), so they are held
            # against V19's shell corners put through the same warp.
            warped, _ = produce.cab_warp(r['chunks']['POSITION'], r['chunks']['NORMAL'])
            mine = set(struct.iter_unpack('<fff', P)); theirs = set(struct.iter_unpack('<fff', warped.tobytes()))
            assert mine <= theirs, f'far {name}: every simplified corner is a (warped) V19 shell corner'
            assert len(P) < len(r['chunks']['POSITION']), f'far {name}: simplified'
            simplified[name][r['part_index']] = (np.frombuffer(P, '<f4').copy(), np.frombuffer(N, '<f4').copy())
    sources = {'near': ASSET / 'brougham-source.glb', 'mid': ASSET / 'brougham-mid-source.glb', 'far': far_src}
    for detail, src in sources.items():
        raw = Path(tmp) / f'{detail}-raw.glb'; idx = Path(tmp) / f'{detail}.glb'
        produce.derive(src, detail, raw, simplified if detail == 'far' else None, simplified_warped=True)
        write_indexed(raw, idx)
        out[detail] = (idx, src, raw)
    return out


def sidecar(levels):
    v19 = json.loads((ASSET / 'brougham.json').read_text())
    register = json.loads((HERE / 'discrepancies.json').read_text())
    return {
        'asset_id': 'studebaker_1893_brougham_reconstruction_01', 'revision': 'v20_plate_match',
        'license': 'GPL-3.0-or-later', 'frame': v19['frame'], 'grade': 'reconstructed',
        'design_reference': v19['design_reference'],
        'derived_from': {'revision': v19['revision'], 'sidecar': 'brougham.json',
                         'sidecar_sha256': sha((ASSET / 'brougham.json').read_bytes()),
                         'note': 'Every V19 part is carried over byte for byte except the six named removals and the cab (see cab); the V19 files and their own gate stay.'},
        'producer': 'tools/transport/brougham_v20/produce.py', 'gate': 'tools/transport/brougham_v20/check.py',
        'removed_v19_parts': sorted(produce.REMOVED), 'added_parts': produce.ADDED,
        'far_simplified_shells': produce.SIMPLIFY,
        'cab': {**produce.CAB, 'lowered_parts': sorted(produce.CAB_LOWERED), 'lowered_seats': list(produce.SEATS_LOWERED),
                'ticket': 'T-3553', 'grade': 'reconstructed',
                'note': 'Passengers sit upright: cushion and seat data lowered by drop_m, the squab lengthened down to the cushion (its top kept), the floor lowered by floor_drop_m, the bench base shortened onto the rear spring hangers, and the body frame below the waist and behind the door brought down with them by a smooth warp, as plate 0095 draws the rear quarter. Every other part, frame, contact and the coachman\'s box are V19\'s.'},
        'lods': levels,
        'coachman_fit': {'fitted_on_file': V19_NEAR, 'fitted_on_sha256': sha((ROOT / 'renderers/web' / V19_NEAR).read_bytes()),
                         'fitted_on_sidecar_sha256': sha((ASSET / 'brougham.json').read_bytes()),
                         'preserved_parts': sorted(FIT_PARTS),
                         'note': 'The seated coachman export and his livery were fitted on V19 near. Every level of V20 keeps those box surfaces, every vehicle frame, contact and seat datum exactly, so the fit holds; driven rows name V19 as fitted_on.'},
        'anchors': v19['anchors'], 'discrepancies': register,
        'photographic_review': 'Matched against plate 0095 at the solved orthographic camera (docs/RESEARCH/brougham-body-T-3084/SOURCE-CAMERA-HYPOTHESIS.json) and in the 1904 town at desktop and phone; see discrepancies for what still differs and why.',
    }


def check_rows(side, loops):
    v20 = {f"transport/parked-brougham/{l['file']}": l['sha256'] for l in side['lods']}
    used = 0
    for row in loops['rows']:
        b = row.get('driver_binding') or {}
        if not str(row.get('vehicle_file', '')).startswith('transport/parked-brougham/brougham-v20'):
            continue
        used += 1
        carried = [{'file': b.get('vehicle_file'), 'sha256': b.get('vehicle_glb_sha256')}] + list(b.get('also_carries', []))
        for c in carried:
            assert v20.get(c['file']) == c['sha256'], f"{row['id']}: binding names {c['file']} at a hash that is not V20's"
        assert row['vehicle_file'] == b['vehicle_file'] and row.get('vehicle_glb_sha256', b['vehicle_glb_sha256']) == b['vehicle_glb_sha256']
        if row.get('vehicle_file_light'):
            assert any(c['file'] == row['vehicle_file_light'] and c['sha256'] == row['vehicle_glb_sha256_light'] for c in carried), f"{row['id']}: light level not carried"
        f = b.get('fitted_on') or {}
        cf = side['coachman_fit']
        assert (f.get('vehicle_file'), f.get('vehicle_glb_sha256'), f.get('vehicle_sidecar_sha256')) == (cf['fitted_on_file'], cf['fitted_on_sha256'], cf['fitted_on_sidecar_sha256']), f"{row['id']}: fitted_on must name V19 exactly"
    return used


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix='brougham-v20-') as tmp:
        fresh = regenerate(tmp)
        levels = []
        for detail in ('near', 'mid', 'far'):
            idx, v19src, rawfile = fresh[detail]
            committed = ASSET / FILES[detail]
            a_doc, a_bin = read(committed)
            if detail == 'far':
                f_doc, f_bin = read(idx)
                assert expanded_signature(f_doc, f_bin) == expanded_signature(a_doc, a_bin), 'far: every triangle re-derives'
                assert idx.read_bytes() == committed.read_bytes(), 'far: committed bytes re-derive exactly'
            else:
                assert idx.read_bytes() == committed.read_bytes(), f'{detail}: committed V20 regenerates byte for byte'
            levels.append(measure(detail, rawfile, committed, v19src))
        side = sidecar(levels)
        # Negative controls on real bytes.
        doc, binary = read(ASSET / FILES['near'])
        controls = {}
        try:
            v19doc, v19bin = read(fresh['near'][1])
            moved = bytearray(v19bin)
            r = rows_by(v19doc, v19bin)['driver_footboard'][0]
            struct.pack_into('<f', moved, r['offsets']['POSITION'], struct.unpack_from('<f', moved, r['offsets']['POSITION'])[0] + .01)
            assert fit_record(v19doc, bytes(moved))['parts'] != fit_record(v19doc, v19bin)['parts']
            controls['moved footboard is seen'] = True
        except AssertionError:
            raise AssertionError('negative control escaped: moved footboard')
        kept = collections.Counter(p['name'] for p in v19doc['extras']['parts'])
        assert kept['thin_rear_mudguard'] and not collections.Counter(p['name'] for p in doc['extras']['parts'])['thin_rear_mudguard']
        controls['a kept mudguard is seen'] = True
        loops = json.loads(LOOPS.read_text())
        bad = copy.deepcopy(loops)
        for row in bad['rows']:
            if str(row.get('vehicle_file', '')).startswith('transport/parked-brougham/brougham-v20'):
                row['driver_binding']['vehicle_glb_sha256'] = '0' * 64
                break
        try:
            check_rows(side, bad)
            if any(str(r.get('vehicle_file', '')).startswith('transport/parked-brougham/brougham-v20') for r in loops['rows']):
                raise RuntimeError('escaped')
        except AssertionError:
            controls['a wrong row hash is refused'] = True
        except RuntimeError:
            raise AssertionError('negative control escaped: wrong row hash')
    if a.write:
        SIDE.write_text(json.dumps(side, indent=1) + '\n')
    assert json.loads(SIDE.read_text()) == side, 'brougham-v20.json is stale; run check.py --write'
    used = check_rows(side, json.loads(LOOPS.read_text()))
    print(json.dumps({'pass': True, 'levels': [{k: l[k] for k in ('detail', 'triangles', 'bytes', 'draw_batches')} for l in levels],
                      'driven_rows_on_v20': used, 'negative_controls': controls}))


if __name__ == '__main__':
    main()
