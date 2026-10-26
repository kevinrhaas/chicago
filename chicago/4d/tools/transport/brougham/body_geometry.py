# SPDX-License-Identifier: GPL-3.0-or-later
"""V19 body refinement must preserve the accepted V18 physical specimen.

The baseline is the immutable accepted cb93 asset, not the new producer's idea
of its own output. Compare serialized occurrence P/N, optics, frames and actual
contacts before accepting fresh hashes. Appearance remains a separate review.
"""
import collections
import copy
import hashlib
import json
import math

OWNED = {('deep_curved_lower_body', 'vehicle_body', 0),
         ('deep_curved_lower_body', 'vehicle_body', 1),
         ('cabin_front_lower', 'vehicle_body', 0),
         ('passenger_cushion', 'vehicle_body', 0),
         ('passenger_back', 'vehicle_body', 0)}
ADDED = {('driver_cushion_edge_piping', 'vehicle_body', 0)}


def part_rows(doc, binary):
    from check_mid import bind_parts
    occurrences = collections.Counter()
    result = {}
    for row in bind_parts(doc, binary):
        name, frame, material, triangles = row['identity']
        key = (name, frame, occurrences[(name, frame)])
        occurrences[(name, frame)] += 1
        result[key] = {'material': material, 'triangles': triangles,
                       **{kind: hashlib.sha256(row['chunks'][kind]).hexdigest()
                          for kind in ['POSITION', 'NORMAL']}}
    return result


def named_frames(doc):
    return [{**{k: v for k, v in node.items() if k != 'children'},
             'named_children': [doc['nodes'][i]['name'] for i in node.get('children', [])
                                if doc['nodes'][i]['name'].startswith('vehicle_')]}
            for node in doc['nodes'] if node['name'].startswith('vehicle_')]


def baseline_record(doc, binary, source_hash):
    from check_near import native_contacts, world_nodes, decoded_bounds
    from static_master import static_master_contract
    rows = part_rows(doc, binary)
    return {'source_sha256': source_hash,
            'parts': [{'key': list(k), **v} for k, v in rows.items()],
            'lamp_iron_glass_quarter_materials': doc['materials'][3:7],
            'named_frames': named_frames(doc),
            'contacts': native_contacts(doc, binary),
            'bounds_m': decoded_bounds(doc, binary, world_nodes(doc)),
            'static_master': static_master_contract(doc, binary, world_nodes(doc), source_hash)}



def normal_only_signatures(doc, binary):
    rows = part_rows(doc, binary)
    encode = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'all_position_streams_sha256': encode([(list(k), rows[k]['POSITION']) for k in sorted(rows)]),
            'other_normal_streams_sha256': encode([(list(k), rows[k]['NORMAL']) for k in sorted(rows) if k[0] != 'cabin_front_lower']),
            'materials_sha256': encode(doc['materials']), 'nodes_sha256': encode(doc['nodes']),
            'source_occurrences': len(rows)}


def check_normal_only(doc, binary):
    from pathlib import Path
    expected = json.loads(Path(__file__).with_name('analytical-normal-only-baseline.json').read_text())
    mode = 'near' if len(doc['extras']['parts']) == 481 else 'mid'
    assert normal_only_signatures(doc, binary) == expected['details'][mode]['signatures'], \
        'Analytical front fix must preserve every C1 position and every other normal/material/frame'
    return True


def check_preservation(doc, binary, baseline):
    from check_near import native_contacts, world_nodes, decoded_bounds
    from static_master import static_master_contract
    actual = part_rows(doc, binary)
    old = {tuple(row['key']): {k: v for k, v in row.items() if k != 'key'}
           for row in baseline['parts']}
    assert set(actual) - set(old) == ADDED and not set(old) - set(actual), 'Exact body-only added inventory'
    changed = {k for k in old if any(actual[k][kind] != old[k][kind] for kind in ['POSITION', 'NORMAL'])}
    assert changed == OWNED, 'Only the five reviewed body/pad occurrences may change geometry'
    for key, row in old.items():
        expected_material = 7 if key[0] in ['side_door_glass', 'front_glass'] else row['material']
        assert actual[key]['material'] == expected_material, 'Unexpected source component material reassignment'
        if key not in OWNED:
            assert actual[key]['triangles'] == row['triangles'], 'Protected source feature tessellation changed'
    assert doc['materials'][3:7] == baseline['lamp_iron_glass_quarter_materials'], 'Accepted lamp optics/iron/quarter changed'
    assert named_frames(doc) == baseline['named_frames'], 'Named frames/transforms/parent hierarchy changed'
    assert native_contacts(doc, binary) == baseline['contacts'], 'Wheel/pole/shoe/hitch contact geometry changed'
    world = world_nodes(doc)
    assert decoded_bounds(doc, binary, world) == baseline['bounds_m'], 'Original native outer envelope changed'
    measured = static_master_contract(doc, binary, world, baseline['source_sha256'])
    assert measured == baseline['static_master'], 'Door/seat references/targets/conservative proxy changed'
    check_normal_only(doc, binary)
    return {'protected_occurrences': len(old) - len(OWNED),
            'changed_body_occurrences': len(OWNED), 'added_piping_occurrences': len(ADDED),
            'accepted_V18_lamps_exact': True, 'contacts_frames_proxy_exact': True}


def mutation_controls(doc, binary, baseline):
    """Exercise actual serialized protected geometry and shared optics in memory."""
    import struct
    from check_mid import bind_parts
    rows = bind_parts(doc, binary)
    protected = next(row for row in reversed(rows) if row['identity'][0] == 'solid_bright_hub_button')
    changed = bytearray(binary)
    offset = protected['offsets']['POSITION']
    struct.pack_into('<f', changed, offset, struct.unpack_from('<f', changed, offset)[0] + .001)
    variants = [('protected final hub geometry', doc, changed)]
    front = next(row for row in rows if row['identity'][0] == 'cabin_front_lower')
    deformed = bytearray(binary)
    offset = front['offsets']['POSITION']
    struct.pack_into('<f', deformed, offset, struct.unpack_from('<f', deformed, offset)[0] + .001)
    variants.append(('owned front position deformation', doc, deformed))
    optics = copy.deepcopy(doc)
    optics['materials'][5]['pbrMetallicRoughness']['roughnessFactor'] += .001
    variants.append(('accepted lamp glazing', optics, binary))
    frames = copy.deepcopy(doc)
    next(n for n in frames['nodes'] if n['name'] == 'vehicle_hitch_team')['translation'][0] += .001
    variants.append(('named hitch frame', frames, binary))
    for name, candidate, payload in variants:
        try:
            check_preservation(candidate, payload, baseline)
        except AssertionError:
            continue
        raise AssertionError('Actual negative control escaped: ' + name)
    return {name: True for name, _, _ in variants}


def check_front_curve(parameters):
    """Independently sample the real front-curve helper: landmarks/range/C1.

    These are mathematical continuity checks, not photographic tolerances.
    Finite differences cross each original source-height bearing from both sides.
    """
    from body_finish import front_outline_curve
    curve, _, knots = front_outline_curve(parameters['lower_side_profile_z_y_m'])
    assert all(abs(curve(y)[0] - z) < 1e-10 for y, z in knots), 'Original front-bearing values changed'
    max_jump = 0.
    for i, ((a, za), (b, zb)) in enumerate(zip(knots, knots[1:])):
        for k in range(33):
            value, slope = curve(a + (b - a) * k / 32)
            assert min(za, zb) - 1e-10 <= value <= max(za, zb) + 1e-10, 'Front interval overshoot'
            assert math.isfinite(value) and math.isfinite(slope)
        if i:
            epsilon = min(a - knots[i - 1][0], b - a) * 1e-6
            left = (curve(a)[0] - curve(a - epsilon)[0]) / epsilon
            right = (curve(a + epsilon)[0] - curve(a)[0]) / epsilon
            jump = abs(left - right)
            max_jump = max(max_jump, jump)
            assert jump < 1e-3, 'Front slope is discontinuous at a source bearing'
    for outside in [knots[0][0] - .001, knots[-1][0] + .001]:
        try:
            curve(outside)
        except ValueError:
            continue
        raise AssertionError('Front extrapolation escaped the original envelope')
    return {'source_height_bearings': len(knots), 'interval_samples': 33 * (len(knots) - 1),
            'max_finite_difference_slope_jump': max_jump, 'landmarks_exact': True,
            'interval_overshoot': False, 'extrapolation_refused': True}
