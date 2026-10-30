"""Fresh binding-v2 qualification. No historical or metadata-only verdict transfer."""
import argparse
import json
from pathlib import Path
import time
import binding_source as child

ROOT, APP = child.ROOT, child.APP
sha, need = child.sha, child.need

def code_pins():
    declared = json.loads((ROOT / 'CODE-PIN-PATHS.json').read_bytes())
    pins = {name: sha((APP / relative).read_bytes()) for name, relative in declared['paths'].items()}
    for name, expected in declared['preserved_old24_expected_sha256'].items():
        need(pins[name] == expected, 'immutable original24 implementation changed: ' + name)
    return pins

def verify_native(source, manifest_path, supervisor_prefix, pins):
    import socket_qualification as q
    original = source.parent_mode.ancestor
    root = manifest_path.parent.resolve()
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    need(manifest['schema'] == 'NEW_binding_v2_native129_capture_v1', 'explicit new binding capture schema')
    need(manifest['candidate_sha256'] == child.CANDIDATE_SHA and manifest['parent_sha256'] == child.PAIRED_SHA,
         'exact newly bound candidate and separately versioned reference')
    need(manifest['immutable_original925_sha256'] == child.generator.REFERENCE_SHA
         and manifest['immutable_motion_source_sha256'] == child.generator.PARENT_SHA, 'immutable source lineage retained')
    need(manifest['physical_loop_sha256'] == child.PHYSICAL_LOOP_SHA and manifest['code_pins'] == pins == code_pins(),
         'original metric and exact new implementation')
    need(manifest['coordinate_frame'] == 'native_getVertexPosition_identity_mesh_bind_canonical_metres', 'actual native frame')
    frames = manifest['frames']
    need(len(frames) == 129, 'all129 actual captured frames')
    for i, row in enumerate(frames):
        need(row['index'] == i and row['time_s'] == i * 3 / 32
             and row['key'] == (i // 2 if i % 2 == 0 else None), 'exact ordered keys and midpoints')
    result_row = manifest['capture_result']
    result_path = (root / result_row['path']).resolve()
    need(result_path.is_relative_to(root), 'capture result containment')
    result_raw = result_path.read_bytes()
    need(sha(result_raw) == result_row['sha256'] and len(result_raw) == result_row['bytes'], 'actual result bytes')
    result = json.loads(result_raw)
    need(result['status'] == 'NEW_BINDING_V2_NATIVE129_CAPTURE_ONLY_COMPLETE', 'actual native capture PASS')
    need(result['candidate_sha256'] == child.CANDIDATE_SHA and result['paired925_reference_sha256'] == child.PAIRED_SHA
         and result['immutable_motion_source_sha256'] == child.generator.PARENT_SHA
         and result['code_pins'] == pins, 'exact result source/code binding')
    for name in ['pageerrors', 'consoleerrors', 'http_errors', 'request_failed', 'closure_errors', 'integrity_errors']:
        need(result[name] == [], 'strict native error ' + name)
    for name in ['context_closed', 'browser_closed', 'server_closed', 'inputs_unchanged']:
        need(result[name] is True, 'actual closed native resource ' + name)
    need(result['WebGL_contexts_created'] == result['WebGL_context_requests'] == 0 and result['socket_frames'] == 129,
         'zero native WebGL requests/contexts and complete raw inventory')
    physical, old13 = result['actual_physical'], result['actual_old13_physical']
    limits = json.loads((original.PACKET / 'ORIGINAL-PHYSICAL-LIMITS.json').read_bytes())
    for report, mode in [(old13, 'old13'), (physical, 'new17')]:
        need(report['status'] == 'LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY'
             and report['key_count'] == 65 and report['midpoint_count'] == 64
             and report['failures'] == [] and len(report['poses']) == 129, 'actual ' + mode + ' all129 physical PASS')
        need(report['binding_mode'] == mode and report['original_physical_limits'] == limits
             and report['WebGL_contexts_created'] == report['renderers_created'] == 0,
             'unchanged original physical limits/no renderer ' + mode)
    parity = old13['old13_parity']
    need(parity['samples'] == 129 and parity['vertices_per_sample'] == 12838
         and parity['tolerance_m'] == 1e-5 and parity['tolerance_degrees'] == .01
         and parity['maximum_position_m'] <= 1e-5 and parity['maximum_shader_normal_degrees'] <= .01
         and parity['maximum_bone_world_component'] == 0, 'all old13 native vertex/shader-normal equivalence')
    need(physical['old13_parity'] == parity and physical['selected_exported_clip_index'] == 1
         and physical['selected_exported_track_count'] == 17
         and physical['selected_exported_clip'] == 'sevket_reconstructed_natural_planted_idle_v1'
         and physical['old_certificate_transferred'] is False, 'actual selected new17 after old13 qualification')
    for joint in [2, 3, 4, 5]:
        first = physical['poses'][0]['world_matrices'][joint]
        change = max(abs(p['world_matrices'][joint][k] - first[k]) for p in physical['poses']
                     for k in [0, 1, 2, 4, 5, 6, 8, 9, 10])
        need(change > .02, 'new17 actual joint rotation advances materially ' + str(joint))
    for suffix in ['.result.json', '.cleanup.json']:
        closed = json.loads(Path(str(supervisor_prefix) + suffix).read_bytes())
        if suffix == '.cleanup.json':
            need(closed['cleanup_complete'] is True and closed['remaining_owned_children'] == [], 'no remaining owned native descendants')
            continue
        need(closed['returncode'] == 0 and closed['timed_out'] is False, 'actual native supervisor PASS')
        command = closed['command']
        need(len(command) == 4 and Path(command[0]).name == 'node'
             and Path(command[1]).resolve() == ROOT / 'run_binding129.cjs'
             and Path(command[3]).resolve() == root and Path(closed['cwd']).resolve() == APP,
             'actual native command/cwd and capture binding')
        static_path = Path(command[2]).resolve()
        static_raw = static_path.read_bytes()
        need(result['static_proof'] == {'path': str(static_path), 'sha256': sha(static_raw), 'bytes': len(static_raw)},
             'actual static proof command/input binding')
        static = json.loads(static_raw)
        need(static['status'] == 'BINDING_V2_CURRENT_SOURCE_STATIC_ONLY_PASS'
             and static['candidate_sha256'] == child.CANDIDATE_SHA
             and static['paired925_sha256'] == child.PAIRED_SHA and static['code_pins'] == pins,
             'same-code fresh static proof')
    components = q.components(source, source.eye)
    allowed, ledger = q.source_interface_faces(source, components)
    baseline = {j for i, j in q.globe_pairs(source.old_body, set(range(len(source.old_body))), source.eye, source.crosses)}
    posed = q.traverse_pose_frames(source, frames, root, allowed, baseline, physical['poses'])
    source.unchanged()
    return {'status': 'BINDING_V2_ACTUAL_OLD13_NEW17_PHYSICAL_AND_PAIRED_SOCKET129_ONLY_PASS',
            'source_admission': child.MODE, 'candidate_sha256': child.CANDIDATE_SHA,
            'paired925_sha256': child.PAIRED_SHA, 'immutable_original925_sha256': child.generator.REFERENCE_SHA,
            'immutable_motion_source_sha256': child.generator.PARENT_SHA,
            'physical_loop_sha256': child.PHYSICAL_LOOP_SHA, 'original_physical_limits': limits,
            'old13_parity': parity, 'actual_old13_physical': old13, 'actual_new17_physical': physical,
            'all129_paired925_posed_frames': posed, 'capture_manifest_sha256': sha(raw),
            'capture_result_sha256': sha(result_raw), 'old_certificate_transferred': False,
            'runtime_adoption': False, 'photographic_acceptance': False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['source', 'static', 'posed'], required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--poses', type=Path)
    parser.add_argument('--supervisor-prefix', type=Path)
    args = parser.parse_args()
    need(not args.out.exists() and not args.out.resolve().is_relative_to(APP.parent.parent), 'fresh outside-app output')
    started = time.monotonic()
    try:
        pins = code_pins()
        source = child.Sources()
        if args.phase == 'source':
            checks = child.audit.controls(source.binding_parent_raw, source.original925_raw,
                                           source.raw[source.binding_path], source.raw[source.paired_path],
                                           source.binding_recipe_raw, source.overlay)
            result = {'status': 'BINDING_V2_SOURCE_CONTROLS_ONLY_PASS', 'controls': checks,
                      'structure': source.structure, 'native129': 'UNRUN', 'paired925_socket129': 'UNRUN'}
        elif args.phase == 'static':
            result = child.static(source)
        else:
            need(args.poses is not None and args.supervisor_prefix is not None, 'actual closed native capture required')
            result = verify_native(source, args.poses, args.supervisor_prefix, pins)
        source.unchanged()
        need(code_pins() == pins, 'new or ancestor implementation changed while executing')
        result.update(code_pins=pins, seconds=time.monotonic() - started, runtime_adoption=False)
        args.out.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({'status': result['status'], 'seconds': result['seconds'], 'output': str(args.out)}))
    except Exception as error:
        if not args.out.exists():
            args.out.write_text(json.dumps({'status': 'FAILED_NEW_BINDING_NO_ADOPTION', 'phase': args.phase,
                                            'error': str(error), 'type': type(error).__name__, 'runtime_adoption': False}, indent=2) + '\n')
        raise

if __name__ == '__main__':
    main()
