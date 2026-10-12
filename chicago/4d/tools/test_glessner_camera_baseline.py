#!/usr/bin/env python3
"""Behavioral checks for the comparison instrument, not house acceptance."""
import copy, hashlib, json, unittest
from unittest.mock import patch
import numpy as np
import glessner_camera_baseline as b

class BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((b.DIRECTORY/'observations.json').read_text())
        cls.report=json.loads((b.DIRECTORY/'report.json').read_text())

    def test_check_points_cannot_move_camera(self):
        # This is a fitting-behavior fixture for the current asset. The committed
        # historical observations/report remain frozen across later model edits.
        fixture=copy.deepcopy(self.data)
        for name,meta in fixture['assets'].items():
            meta['sha256']=hashlib.sha256((b.ROOT/name).read_bytes()).hexdigest()
        reference=b.derive(fixture)
        changed=copy.deepcopy(fixture)
        for view in changed['views']:
            for point in view['landmarks']:
                if point['role']=='check':point['observed_px'][0]+=7
        actual=b.derive(changed)
        for old,new in zip(reference['views'],actual['views']):
            self.assertEqual(old['camera'],new['camera'])
            self.assertNotEqual(old['check_rms_px'],new['check_rms_px'])

    def test_changed_asset_is_not_a_frozen_baseline(self):
        changed=copy.deepcopy(self.data)
        next(iter(changed['assets'].values()))['sha256']='0'*64
        with self.assertRaisesRegex(AssertionError,'Baseline asset drift'):
            b.validate(changed)

    def test_duplicate_pixels_do_not_count_as_coverage(self):
        changed=copy.deepcopy(self.data)
        changed['views'][0]['landmarks'][1]['observed_px']=changed['views'][0]['landmarks'][0]['observed_px']
        with self.assertRaisesRegex(AssertionError,'Repeated source picks'):b.validate(changed,False)

    def test_candidate_uses_frozen_cameras_without_optimizer(self):
        with patch.object(b,'least_squares',side_effect=AssertionError('Candidate must never refit')):
            result=b.evaluate_candidate(self.data,self.report,b.ROOT/'assets/gltf/glessner_house__as_built_1887.glb')
        self.assertFalse(result['camera_refitted'])
        for old,new in zip(self.report['views'],result['views']):
            self.assertEqual(old['camera'],new['camera'])
            for a,z in zip(old['landmarks'],new['landmarks']):
                self.assertEqual(a['residual_px'],z['baseline_residual_px'])
                self.assertEqual(a['observed_px'],z['observed_px'])
                # Later geometry may genuinely change the candidate residual.
                # Its reported error must measure the actual projected point.
                distance=np.linalg.norm(np.array(z['predicted_px'])-z['observed_px'])
                self.assertAlmostEqual(distance,z['residual_px'],places=3)

    def test_extrapolated_width_cannot_manufacture_pass(self):
        changed=copy.deepcopy(self.report)
        changed['views'][0]['projected_width_px']=1e9
        changed['views'][0]['observed_span_px']=1
        result=b.evaluate_candidate(self.data,changed,b.ROOT/'assets/gltf/glessner_house__as_built_1887.glb')
        point=result['views'][0]['landmarks'][0]
        self.assertLess(point['fraction_baseline_projected_width'],.01)
        self.assertGreater(point['fraction_observed_span'],.01)
        self.assertFalse(point['target_met'])

    def test_camera_frame_and_metric_orientation(self):
        np.testing.assert_allclose(b.metric([0,0,0]),[49.149,22.5552,0])
        for v in self.report['views']:
            axes=np.array(v['camera']['basis_right_up_forward'])
            np.testing.assert_allclose(axes@axes.T,np.eye(3),atol=1e-9)
            self.assertGreater(v['fit_controls'],3)
            self.assertGreater(v['check_points'],0)

if __name__=='__main__':unittest.main()
