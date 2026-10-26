"""Prepare source runtime metadata for the independently qualified anatomy GLB.

No publishing, Git, ticket or network operations. Source originals and old
receipts remain immutable. Contact samples are rebuilt from the selected mesh,
including every descendant of the original witness faces and an independent
10mm clipped sole slab. World/phone/photographic acceptance remains pending.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

APP = Path(__file__).resolve().parents[2]
AUTHORED = APP / 'assets/authored/transport/horse_standing'
sys.path.insert(0, str(AUTHORED))
import generate_anatomy_v2 as anatomy

SHA = lambda b: hashlib.sha256(b).hexdigest()
CHILD_SHA = '925fac957110b9b57b95c5abfed17fabf29f868b173f38f0569d984dd9999a48'
NAME = 'horse-sevket-anatomy-v2.glb'


def unique(points):
    output = {}
    for point in points:
        output.setdefault(tuple(round(x, 12) for x in point), list(point))
    return list(output.values())


def polygon_samples(points):
    if len(points) < 3:
        return []
    result = list(points)
    result += [tuple((a[k] + b[k]) / 2 for k in range(3))
               for a, b in zip(points, points[1:] + points[:1])]
    result.append(tuple(sum(p[k] for p in points) / len(points) for k in range(3)))
    return result


def clip_below(points, ceiling):
    output = []
    for a, b in zip(points, points[1:] + points[:1]):
        ai, bi = a[1] <= ceiling, b[1] <= ceiling
        if ai:
            output.append(a)
        if ai != bi:
            t = (ceiling - a[1]) / (b[1] - a[1])
            output.append(tuple(a[k] + t * (b[k] - a[k]) for k in range(3)))
    return output


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate-dir', type=Path, required=True)
    parser.add_argument('--physical-result', type=Path, required=True)
    parser.add_argument('--physical-config', type=Path, required=True)
    args = parser.parse_args()
    candidate_file = args.candidate_dir / NAME
    raw = candidate_file.read_bytes()
    assert SHA(raw) == CHILD_SHA
    derivation = json.loads((args.candidate_dir / 'DERIVATION-RECEIPT.json').read_text())
    assert derivation['candidate_sha256'] == CHILD_SHA
    result_bytes = args.physical_result.read_bytes()
    result, config = json.loads(result_bytes), json.loads(args.physical_config.read_text())
    assert result['status'] == 'FRESH_NEW_BODY_LOADED129_PHYSICAL_PASS_ONLY'
    assert config['inputs']['candidate']['sha256'] == CHILD_SHA
    assert result['config_sha256'] == SHA(args.physical_config.read_bytes())
    assert all(result[k] for k in ['inputs_unchanged', 'context_closed', 'browser_closed', 'server_closed'])
    assert all(not result[k] for k in ['pageerrors', 'consoleerrors', 'http_errors', 'closure_errors', 'integrity_errors'])
    actual = result['actual']
    assert actual['key_count'] == 65 and actual['midpoint_count'] == 64 and not actual['failures']
    assert actual['original_physical_limits']['stance_patch_drift_m'] == 1e-5
    assert actual['original_physical_limits']['minimum_all_surface_y_m'] == -1e-5

    document, binary = anatomy.base.read_glb(raw)
    attributes = document['meshes'][1]['primitives'][0]['attributes']
    positions = anatomy.read_attribute(document, binary, attributes['POSITION'])
    indices = [v[0] for v in anatomy.read_attribute(document, binary, document['meshes'][1]['primitives'][0]['indices'])]
    triangles = [indices[i:i + 3] for i in range(0, len(indices), 3)]
    parent_bytes = (APP / 'tools/fixtures/horse-anatomy-parent-sidecar-v1.json').read_bytes()
    assert SHA(parent_bytes) == '4ec44024d4fbefae88b8f0a1deb3be92503768b65dba590c5762691ce3b9c924'
    parent = json.loads(parent_bytes)
    spec = copy.deepcopy(parent)
    face_map = derivation['source_boundary']['hoof_refinement']['source_face_to_children']
    centres = {}
    for name, patch in parent['contacts'].items():
        ids = sorted(set(i for face in patch['source_triangle_ids'] for child in face_map[face] for i in triangles[child]))
        centres[name] = tuple(sum(positions[i][k] for i in ids) / len(ids) for k in range(3))
    for name, patch in spec['contacts'].items():
        old_faces = list(patch['source_triangle_ids'])
        selected_faces = sorted(child for face in old_faces for child in face_map[face])
        ids = sorted(set(i for face in selected_faces for i in triangles[face]))
        samples = unique([point for face in selected_faces for point in polygon_samples([positions[i] for i in triangles[face]])])
        ceiling = min(positions[i][1] for i in ids) + .01
        slab = []
        for tri in triangles:
            points = [positions[i] for i in tri]
            if min(p[1] for p in points) > ceiling:
                continue
            centre = tuple(sum(p[k] for p in points) / 3 for k in range(3))
            nearest = min(centres, key=lambda other: (centre[0] - centres[other][0]) ** 2 + (centre[2] - centres[other][2]) ** 2)
            if nearest == name:
                slab.extend(polygon_samples(clip_below(points, ceiling)))
        patch['parent_source_triangle_ids'] = old_faces
        patch['source_triangle_ids'] = selected_faces
        patch['selected_contact_vertex_ids'] = ids
        patch['samples_m'] = samples
        patch['equal_10mm_slab_samples_m'] = unique(slab)
        patch['minimum_vertex_canonical_m'] = list(positions[patch['minimum_vertex_id']])
        patch['index_basis'] = 'Selected anatomy-v2 body primitive; parent source indices retained separately'
        patch['status'] = 'Fresh selected-surface samples; canonical Mixer129 passed; actual drawn-yard support qualification pending'
    spec['contact_mesh']['vertices'] = len(positions)
    spec['source_inventory']['triangles'] = sum(document['accessors'][p['indices']]['count'] // 3
                                               for mesh in document['meshes'] for p in mesh['primitives'])
    assert spec['source_inventory']['triangles'] <= spec['budget_proposal']['maximum_triangles']
    assert len(raw) <= spec['budget_proposal']['maximum_source_bytes']
    spec['status'] = 'Source-bounded eyelid and rounded hoof anatomy derivative. Fresh selected-SHA native views and full Mixer129 physical proof complete; app/yard/phone/world and photographic surface qualification remain pending.'
    spec['source_pose'] = 'Canonical metre source with unchanged reconstructed26 rig/V16 original skin rows and planted-standing clip; locally refined body topology, declared interpolated added rows and source-bounded eyelid rest surface. No walking or original six-clip composition.'
    spec['runtime_asset'].update(file='transport/standing-horse/' + NAME, sha256=CHILD_SHA, bytes=len(raw),
                                anatomy_parent_sha256=anatomy.base.PARENT_SHA256,
                                anatomy_recipe_file='assets/authored/transport/horse_standing/anatomy-v2-recipe.json',
                                anatomy_derivation_summary_file='transport/parked/standing-horse-planted/anatomy-r3-derivation-summary.json')
    spec['runtime_asset']['eye_uv_derivation_receipt_applies_to_sha256'] = anatomy.base.PARENT_SHA256
    spec['runtime_asset']['field_sha256_scope'] = 'Ancestral V16 field for the 4313 original body vertex rows only; added rows use the declared parent-edge four-influence interpolation, freshly qualified on the selected anatomy master.'
    spec['material_variants']['organic_dielectric_v1']['change_notice'] = ('The original model materials use a declared dielectric adaptation. '
        'The eyelid and hoof surfaces have been refined against cleared anatomical references; coat, markings and grooming remain reconstructed. '
        'Source textures are unchanged, and the opaque hair and coat appearance remain under review.')
    spec['known_quality_limits'] = ['Generic reconstructed working animal; no historical individual, breed, owner or calibrated period dimensions.',
        'Resting upper eyelid still reads heavy; source texture/normal-map appearance must be separated from geometry in the surface qualification.',
        'Solid mane and pointed opaque sheet tail, existing coat highlights and 1K maps remain for the sequential T-3089 surface/LOD qualification.',
        'Canonical loaded standing proof is not continuous collision, actual yard/mobile/GPU/performance or full photographic acceptance.',
        'Unseen sole construction, shoeing and loaded tack are not established by these sources.']
    spec['contact_annotation_history']['parent_d454_contact_annotations_sha256'] = SHA(parent_bytes)
    spec['contact_annotation_history']['historical_scope'] = 'Pre-anatomy paragraphs and original receipts describe b479/d454 only; selected-body topology, samples and qualification are superseded explicitly below.'
    spec['contact_annotation_history']['anatomy_supersession'] = 'Selected toe/wall geometry, contact face domain and finite samples are regenerated from the actual anatomy master. Original annotations/receipts remain in the frozen parent fixture; no old body/ground proof is relabelled.'
    spec['proposed_static_support_pose']['parent_finite_sample_qualification'] = spec['proposed_static_support_pose'].pop('finite_sample_qualification')
    spec['proposed_static_support_pose']['finite_sample_qualification'] = {'status': 'Pending fresh actual drawn-yard evaluation of selected-surface samples; retained support quaternion is not an inherited ground acceptance.'}
    spec['ground_support']['status'] = 'Existing bounded terrain-snapshot policy retained; fresh selected-body actual yard support and phone/world checks pending.'

    summary = {key: actual[key] for key in ['status', 'key_count', 'midpoint_count', 'positions', 'normals', 'joint_world',
        'physical', 'loop', 'negative_controls', 'neutral_residual_m', 'original_patch_counts', 'new_patch_counts', 'original_physical_limits']}
    surfaces = [surface for pose in actual['poses'] for surface in pose['surfaces']]
    summary.update(schema='standing-horse-anatomy-r3-loaded129-summary-v1', selected_asset_sha256=CHILD_SHA,
        selected_asset_bytes=len(raw), raw_result_sha256=SHA(result_bytes), failures=[],
        triangle_edge_ratio_range=[min(s['edgeMin'] for s in surfaces), max(s['edgeMax'] for s in surfaces)],
        triangle_area_ratio_range=[min(s['areaMin'] for s in surfaces), max(s['areaMax'] for s in surfaces)],
        reversed_triangles=sum(s['negative'] for s in surfaces), minimum_surface_y_m=min(s['minY'] for s in surfaces),
        owned_resources_closed=True, inputs_unchanged=True, old_body_pass_inherited=False,
        world_or_photographic_acceptance=False, scope='Actual native GLTFLoader/SkeletonUtils clone/Mixer65keys+64midpoints, all selected faces and original/refined contact witnesses under unchanged limits. No world/phone/performance/photographic or gait approval.')
    summary_path = APP / 'data/transport/parked/standing-horse-planted/anatomy-r3-loaded129-summary.json'
    write(summary_path, summary)
    spec['idle']['historical_d454_qualification'] = copy.deepcopy(parent['idle'])
    spec['idle'].update(loaded_qualification_status='FRESH_NEW_BODY_LOADED129_PHYSICAL_PASS_ONLY',
        loaded_qualification_file='transport/parked/standing-horse-planted/anatomy-r3-loaded129-summary.json',
        loaded_qualification_sha256=SHA(summary_path.read_bytes()), loaded_raw_result_sha256=SHA(result_bytes),
        activation_note='Current anatomy master freshly loaded and production-cloned for actual canonical Mixer129 physical checking. App/yard/phone/GPU/performance and photographic qualification are separate; no 1904 placement is added.')
    spec['anatomy'] = {'ticket':'T-3088', 'parent_sha256':anatomy.base.PARENT_SHA256, 'recipe_revision':'r3_original_cage_and_thinner_upper_margin',
        'source_ids':['ellenberger_baum_dittrich_equine_plates','seton_1892_equine_skeleton','vassil_2014_konik_horse_anatomy','joselodos_2025_horse_anatomy'],
        'liberty':'L-horse-anatomy-master-3088', 'static_master_photo_acceptance':False, 'surface_lod_ticket':'T-3089'}
    for source_id in spec['anatomy']['source_ids']:
        source = json.loads((APP / 'data/sources' / (source_id + '.json')).read_text())
        spec['citation_records'][source_id] = {**source, 'source_id': source_id}
    for target in [AUTHORED / NAME, APP / 'renderers/web/transport/standing-horse' / NAME]:
        assert not target.exists(), 'Do not overwrite a previous master'
        shutil.copyfile(candidate_file, target)
    write(APP / 'data/transport/parked/horse-sevket-sidecar.json', spec)
    placement_path = APP / 'data/transport/parked/standing-horses.json'
    placement = json.loads(placement_path.read_text())
    placement['models']['sevket_horse_standing_development_01']['file'] = 'transport/standing-horse/' + NAME
    placement['status'] = 'Same reconstructed1835 horse placement selects the source-bounded anatomy master; fresh current-SHA native views and canonical physical proof, with app/yard/phone and full static surface/LOD photographic qualification pending.'
    placement['scenes']['1835'][0]['support_note'] = 'Retained reconstructed whole-root0.396145-degree support transform; selected-source contact samples are regenerated. No per-leg placement offset; fresh actual-yard qualification required.'
    write(placement_path, placement)
    source_path = AUTHORED / 'SOURCE.json'
    source = json.loads(source_path.read_text())
    source['preserved_d454_parent_derivative'] = copy.deepcopy(source['runtime_derivative'])
    source['runtime_derivative'] = copy.deepcopy(spec['runtime_asset'])
    source['authored_exception'] = 'Licensed third-party canonical authored-mesh derivative with immutable parent, cleared anatomy references, repeatable stdlib anatomy recipe and fresh selected-body physical proof. Original-source/canonical26 authoring recovery remains credited; no procedural regression horse substitutes for this master.'
    source['runtime_adaptations'].append('Source-bounded upper-eyelid rest margin and adaptive rounded hoof wall/coronet/toe topology; original eyes/UVs/maps/rig/clip preserved, added skin/UV rows explicitly interpolated and freshly qualified through native Mixer129.')
    write(source_path, source)
    derivation_summary = {'schema':'standing-horse-anatomy-r3-derivation-summary-v1', 'parent_sha256':anatomy.base.PARENT_SHA256,
        'candidate_sha256':CHILD_SHA, 'candidate_bytes':len(raw), 'raw_derivation_receipt_sha256':SHA((args.candidate_dir/'DERIVATION-RECEIPT.json').read_bytes()),
        'body_vertices':len(positions), 'body_triangles':len(triangles), 'whole_animal_triangles':spec['source_inventory']['triangles'],
        'source_face_parent_count':len(face_map), 'added_vertices':len(positions)-4313,
        'named_anchors_preserved':True, 'all_parent_BIN_bytes_preserved':True, 'body_topology_changed':True,
        'fresh_loaded129_summary_sha256':SHA(summary_path.read_bytes()), 'photographic_acceptance':False,
        'contact_sample_counts':{name:{'surface':len(p['samples_m']),'independent10mm':len(p['equal_10mm_slab_samples_m'])} for name,p in spec['contacts'].items()}}
    write(APP/'data/transport/parked/standing-horse-planted/anatomy-r3-derivation-summary.json', derivation_summary)
    print(json.dumps(derivation_summary))


if __name__ == '__main__':
    main()
