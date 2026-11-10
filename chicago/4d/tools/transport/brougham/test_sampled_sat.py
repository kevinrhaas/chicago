# SPDX-License-Identifier: GPL-3.0-or-later
"""Native numerical/integration controls only; never geometry qualification."""
import json
import math
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

import check_door_aperture as checker
from sampled_sat import separation_batch, BATCH_CAP


def verify():
    tolerance = 1e-8
    a = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
    cases = [('identical', a, a), ('shared_vertex', a, a + [1, 0, 0]),
             ('shared_edge', a, np.array([[0., 0., 0.], [1., 0., 0.], [0., -1., 0.]])),
             ('coplanar_disjoint', a, a + [3, 0, 0]), ('parallel_separate', a, a + [0, 0, .1])]
    for z in [0., tolerance, np.nextafter(tolerance, 0.), np.nextafter(tolerance, math.inf),
              tolerance * (1 - 1e-6), tolerance * (1 + 1e-6), 2 * tolerance]:
        cases.append(('contact_boundary_' + repr(z), a, a + [0, 0, z]))
    for edge in [np.nextafter(1e-14, 0.), 1e-14, np.nextafter(1e-14, math.inf)]:
        cases.append(('axis_cutoff_' + repr(edge), a * [1, edge, 1], a * [1, edge, 1] + [0, 0, 1e-7]))
    fallbacks = 0
    for name, left, right in cases:
        try:
            expected = checker.separation(left, right)
        except ValueError:
            try:
                separation_batch([left], [right], scalar=checker.separation, decision_thresholds=tolerance)
            except ValueError:
                continue
            raise AssertionError('Batch manufactured clearance for scalar-invalid geometry')
        actual, info = separation_batch([left], [right], scalar=checker.separation, decision_thresholds=tolerance)
        assert (actual[0] <= tolerance) == (expected <= tolerance), name
        assert abs(actual[0] - expected) <= info['max_roundoff_guard_m'], name
        if name.startswith('contact_boundary_') and abs(expected - tolerance) < 1e-13:
            assert info['scalar_fallback_rows'] == 1 and actual[0] == expected
        fallbacks += info['scalar_fallback_rows']

    # Exercise the actual sampled checker wrapper across its2048-pair boundary.
    # Native candidate indices stay ordered, including contacts in the last batch.
    fixed = np.tile(a + [0, 0, .1], (BATCH_CAP + 3, 1, 1))
    expected_indices = [1, BATCH_CAP - 1, BATCH_CAP, BATCH_CAP + 2]
    fixed[expected_indices] = a
    contacts = []; batches = 0; pairs = 0
    for indices, gaps, info in checker.sampled_pair_batches(a, fixed, np.arange(len(fixed)), tolerance):
        batches += 1; pairs += info['pairs']
        contacts.extend(int(indices[k]) for k in np.flatnonzero(gaps <= tolerance))
        assert info['owned_workspace_upper_bound_bytes'] <= 16 * 1024 * 1024
    assert contacts == expected_indices and batches == 2 and pairs == len(fixed)
    assert not list(checker.sampled_pair_batches(a, fixed, np.array([], dtype=int), tolerance))
    for bad in [np.zeros((BATCH_CAP + 1, 3, 3)), np.zeros((1, 4, 3))]:
        try:
            separation_batch(bad, bad, scalar=checker.separation, decision_thresholds=tolerance)
        except ValueError:
            continue
        raise AssertionError('Unbounded/malformed batch accepted')

    # Orchestration-only fixtures deliberately mock the already separately tested
    # structural prefix. This proves the diagnostic cannot run interval_clear or
    # emit final PASS, even when every requested discrete sample is clear.
    diagnostics = []
    for has_contact in [False, True]:
        static = a if has_contact else a + [20, 0, 0]
        moving = np.array([True, False]); triangles = np.array([a, static])
        structure = {'schema': 'UNIT_ORCHESTRATION_FIXTURE_NOT_GEOMETRY_PROOF', 'result': 'STRUCTURE_ONLY_PASS'}
        data = ({'open_angle_deg': -65}, {}, b'', [], triangles, moving, ['moving', 'fixed'], np.array([a]), np.array([static]))
        with tempfile.TemporaryDirectory(prefix='t2797-sampled-unit-') as folder:
            p = Path(folder); source = Path(__file__)
            args = SimpleNamespace(input=source, candidate=source, recipe=source, source_receipt=source,
                report=p / 'diagnostic.json', progress=None, max_depth=12, tolerance=tolerance,
                structure_only=False, sampled_only=True)
            with patch.object(checker, 'verify_structure', return_value=(structure, data)), patch.object(
                    checker, 'interval_clear', side_effect=AssertionError('Diagnostic must not run interval proof')) as interval:
                exit_clear_at_samples = checker.check(args)
                interval.assert_not_called()
            result = json.loads(args.report.read_text())
            progress = json.loads(Path(str(args.report) + '.progress.json').read_text())
            assert result['schema'] == 'chicago-brougham-sampled-pose-diagnostic-v1'
            assert result['PASS'] is result['final_PASS'] is result['continuous_interval_run'] is False
            assert progress['final_PASS'] is progress['sweep_qualification_complete'] is False
            assert len(result['sampled']) == 15 and result['sampled'][0]['angle_deg'] == 0
            assert abs(result['sampled'][-1]['angle_deg'] + 65) < 1e-12
            assert exit_clear_at_samples is (not has_contact)
            assert len(result['failure_examples']) == (12 if has_contact else 0)
            diagnostics.append({'contact_fixture': has_contact, 'fifteen_samples_completed': True,
                                'interval_not_called': True, 'final_PASS_false': True})
    return {'schema': 'chicago-brougham-native-sampled-sat-controls-v1', 'result': 'NUMERICAL_INTEGRATION_CONTROLS_PASS',
            'named_scalar_branch_cases': len(cases), 'scalar_fallback_rows': fallbacks,
            'ordered_native_candidate_pairs': pairs, 'ordered_batch_boundary_contacts': contacts,
            'diagnostic_orchestration_controls': diagnostics,
            'actual_door_geometry_or_sweep_qualified': False}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
