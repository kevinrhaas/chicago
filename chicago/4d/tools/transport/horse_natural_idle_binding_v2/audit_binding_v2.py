"""Independent byte-domain admission and source-corruption checks, no poses."""
import copy
import importlib.util
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('binding_generator', ROOT / 'generate_natural_planted_binding_v2.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

def audit(parent_raw, original_raw, candidate_raw, paired_raw, recipe_raw, overlay):
    recipe = json.loads(recipe_raw)
    pd, pb = g.read_glb(parent_raw)
    rd, rb = g.read_glb(original_raw)
    cd, cb = g.read_glb(candidate_raw)
    sd, sb = g.read_glb(paired_raw)
    g.need(g.sha(parent_raw) == g.PARENT_SHA and g.sha(original_raw) == g.REFERENCE_SHA,
           'immutable exact source parents')
    g.need(len(candidate_raw) <= 4194304 and len(paired_raw) <= 4194304, 'unchanged master byte cap')
    changed_bytes = []
    for source_doc, source_bin, child_doc, child_bin, source_sha, role in [
            (pd, pb, cd, cb, g.PARENT_SHA, 'natural-idle-candidate'),
            (rd, rb, sd, sb, g.REFERENCE_SHA, 'paired-original925-geometry-reference')]:
        clean = copy.deepcopy(child_doc)
        notice = clean['asset']['extras'].pop(g.NOTICE)
        g.need(notice == {'source_parent_sha256': source_sha, 'recipe_sha256': g.sha(recipe_raw),
                         'binding_version': 2, 'role': role, 'qualification': 'UNRUN', 'old_certificate_transferred': False},
               'exact honest binding notice')
        g.need(clean == source_doc, 'all rest geometry, rig, clips and unlisted metadata unchanged')
        g.need(len(source_bin) == len(child_bin), 'no appended or hidden BIN streams')
        allowed_bytes = set()
        for mesh in range(3):
            ps = {name: g.stream(source_doc, source_bin, mesh, name) for name in ('JOINTS_0', 'WEIGHTS_0')}
            cs = {name: g.stream(child_doc, child_bin, mesh, name) for name in ('JOINTS_0', 'WEIGHTS_0')}
            expected = {row['row']: row for row in overlay.get(str(mesh), [])}
            label = 'HAIR' if mesh == 0 else 'BODY'
            domain = (set(recipe['allowed_row_masks'][label + '_head_neck']) |
                      set(recipe['allowed_row_masks']['HAIR_original_tail_component' if mesh == 0 else 'BODY_tail_dock'])) if mesh < 2 else set()
            for row in expected:
                g.need(row in domain, 'actual overlay row inside independently reviewed anatomical domain')
            head_rows = set(recipe['allowed_row_masks'][label + '_head_neck']) if mesh < 2 else set()
            for row in range(len(ps['JOINTS_0']['rows'])):
                actual_j, actual_w = cs['JOINTS_0']['rows'][row], cs['WEIGHTS_0']['rows'][row]
                old_j, old_w = ps['JOINTS_0']['rows'][row], ps['WEIGHTS_0']['rows'][row]
                desired = expected.get(row, {'joints': old_j, 'weights': old_w})
                g.need(actual_j == desired['joints'] and actual_w == desired['weights'], 'exact reviewed tuple overlay and all outside tuples')
                g.need(all(w >= 0 for w in actual_w) and abs(sum(actual_w) - sum(old_w)) < 2e-7,
                       'finite positive preserved mass')
                g.need(all(w == 0 or 0 <= joint < 26 for joint, w in zip(actual_j, actual_w)), 'real bone palette')
                if row not in expected:
                    continue
                palette = {1, 2, 3} if row in head_rows else {1, 4, 5}
                for slot, (joint, weight) in enumerate(zip(old_j, old_w)):
                    if joint not in palette and weight > 0:
                        g.need(actual_j[slot] == joint and struct.pack('<f', actual_w[slot]) == struct.pack('<f', weight),
                               'all positive other influences including tiny weights preserved in exact slots')
                for semantic in ('JOINTS_0', 'WEIGHTS_0'):
                    info = ps[semantic]
                    start = info['start'] + row * info['stride']
                    allowed_bytes.update(range(start, start + info['size']))
        count = 0
        for offset, (a, b) in enumerate(zip(source_bin, child_bin)):
            if a != b:
                g.need(offset in allowed_bytes, 'only actual declared JOINTS/WEIGHTS row bytes may change')
                count += 1
        changed_bytes.append(count)
    for mesh in range(3):
        for semantic in ('JOINTS_0', 'WEIGHTS_0'):
            a, b = g.stream(cd, cb, mesh, semantic), g.stream(sd, sb, mesh, semantic)
            g.need(a['rows'] == b['rows'], 'entire paired925 and candidate skin tuples exactly equal')
    return {'status': 'INDEPENDENT_STATIC_BYTE_DOMAIN_ONLY_PASS', 'changed_BIN_bytes_candidate_paired': changed_bytes,
            'all_geometry_rig_IBM_images_UV_normals_materials_clips_exact': True,
            'all_outside_rows_exact_including_3968_EYE': True, 'entire_paired_skin_streams_equal': True,
            'poses': 'UNRUN', 'runtime_adoption': False}

def controls(parent, original, candidate, paired, recipe, overlay):
    passed = []
    cd, cb = g.read_glb(candidate)
    pd, pb = g.read_glb(parent)
    rd, rb = g.read_glb(paired)
    def refuse(label, bad_candidate=candidate, bad_paired=paired):
        try:
            audit(parent, original, bad_candidate, bad_paired, recipe, overlay)
        except (ValueError, KeyError, IndexError):
            passed.append(label)
            return
        raise AssertionError('source corruption admitted: ' + label)
    def bin_damage(label, offset):
        b = bytearray(cb)
        b[offset] ^= 1
        refuse(label, g.write_glb(cd, b))
    # These are actual emitted source corruptions, with the original admission
    # untouched. They include allowed-domain abuse and protected source changes.
    positions = g.stream(cd, cb, 1, 'POSITION')['rows']
    ground_row = min(range(len(positions)), key=lambda i: positions[i][1])
    for label, mesh, semantic, row in [
            ('ground_contact_BODY_weights_changed', 1, 'WEIGHTS_0', ground_row),
            ('EYE_weights_changed', 2, 'WEIGHTS_0', 0),
            ('BODY_rest_geometry_changed', 1, 'POSITION', 1300),
            ('HAIR_normal_changed', 0, 'NORMAL', 0)]:
        a = g.stream(cd, cb, mesh, semantic)
        bin_damage(label, a['start'] + row * a['stride'])
    a = g.stream(cd, cb, 1, 'WEIGHTS_0')
    bin_damage('tiny_positive_leg_influence_changed', a['start'] + 3200 * a['stride'] + 4)
    a = g.stream(cd, cb, 1, 'JOINTS_0')
    b = bytearray(cb)
    struct.pack_into('<H', b, a['start'] + 1300 * a['stride'], 255)
    refuse('positive_joint_out_of_actual_palette', g.write_glb(cd, b))
    a = g.stream(cd, cb, 1, 'WEIGHTS_0')
    b = bytearray(cb)
    struct.pack_into('<f', b, a['start'] + 1300 * a['stride'], -.25)
    refuse('negative_authored_mass', g.write_glb(cd, b))
    a = g.stream(rd, rb, 1, 'WEIGHTS_0')
    b = bytearray(rb)
    b[a['start'] + 1300 * a['stride']] ^= 1
    refuse('paired925_binding_mismatch', bad_paired=g.write_glb(rd, b))
    for label, mutate in [
            ('old_clip_changed', lambda d: d['animations'][0].update(name='bad')),
            ('material_changed', lambda d: d['materials'][0].update(alphaMode='BLEND')),
            ('rig_pivot_changed', lambda d: d['nodes'][2].update(translation=[0, 0, 0])),
            ('false_certificate_transfer', lambda d: d['asset']['extras'][g.NOTICE].update(old_certificate_transferred=True))]:
        bad = copy.deepcopy(cd)
        mutate(bad)
        refuse(label, g.write_glb(bad, cb))
    g.need(len(passed) == 12, 'all twelve meaningful source corruptions executed')
    return passed
