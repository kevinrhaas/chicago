# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepared-source contact tests; no Blender or exported-skin acceptance claim."""
import copy,json,math,os,pathlib,types,unittest
from human_grounded_gait import (prepare_legs,pose_at_phase,foot_trajectory,linearize_action,
                                 CYCLE_FRAMES,CYCLE_DURATION_S,SPEED_M_S)
from measure_grounded_sampling import measure

class GroundedGaitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=pathlib.Path(os.environ.get('C4D_GAIT_BODY_DIRECTORY',pathlib.Path(__file__).resolve().parents[1]/'assets/authored/humans/makehuman_hm08'))
        cls.bodies={age:json.loads((base/f'prepared_adult_{age}.json').read_text())for age in(25,35)}
    def test_real_prepared_bodies_dense_and_30fps_contact(self):
        self.assertEqual(CYCLE_FRAMES,36);self.assertEqual(CYCLE_DURATION_S,1.2);self.assertEqual(SPEED_M_S,.6)
        for age,body in self.bodies.items():
            for mode in ('dense','keys30fps_slerp'):
                with self.subTest(age=age,mode=mode):
                    r=measure(body,mode)
                    self.assertLess(r['max_planted_sole_world_drift_m'],.001)
                    self.assertLess(r['max_supported_sole_height_error_m'],.0005)
                    self.assertGreater(r['minimum_sole_height_m'],-.0005)
                    self.assertEqual(r['phases_without_support'],0)
                    self.assertLess(r['sole_loop_closure_m'],1e-12)
                    self.assertGreater(r['minimum_forward_knee_pole_m'],0)
    def test_stance_trajectory_preserves_root_compensated_position(self):
        positions=[foot_trajectory(q,0)[1]+SPEED_M_S*CYCLE_DURATION_S*q for q in (0,.1,.3,.6)]
        self.assertLess(max(positions)-min(positions),1e-12)
    def test_loops_and_actual_lengths_remain_unchanged(self):
        for body in self.bodies.values():
            original=copy.deepcopy(body['skeleton']);bones={b['name']:b for b in body['skeleton']};legs=prepare_legs(bones)
            a,b=pose_at_phase(legs,0),pose_at_phase(legs,1)
            self.assertEqual(a['pelvis_delta_m'],b['pelvis_delta_m']);self.assertEqual(a['x_rotations_rad'],b['x_rotations_rad'])
            self.assertEqual(body['skeleton'],original)
            for side in ('l','r'):
                self.assertAlmostEqual(sum(a['x_rotations_rad'][n+'_'+side]for n in('thigh','calf','foot')),0,places=12)
    def test_refuses_unreviewed_nonvertical_rest_frame(self):
        bones={b['name']:copy.deepcopy(b)for b in self.bodies[25]['skeleton']};bones['calf_l']['head_m'][2]+=.01
        with self.assertRaises(ValueError):prepare_legs(bones)
    def test_refuses_unreachable_targets_and_invalid_inputs(self):
        bones={b['name']:b for b in self.bodies[25]['skeleton']};small=prepare_legs(bones,.1)
        with self.assertRaises(ValueError):pose_at_phase(small,.25)
        with self.assertRaises(ValueError):pose_at_phase(prepare_legs(bones),float('nan'))
        with self.assertRaises(ValueError):prepare_legs(bones,float('nan'))
    def test_legacy_and_blender45_layered_curves_explicit_linear(self):
        key=lambda:types.SimpleNamespace(interpolation='BEZIER')
        legacy=types.SimpleNamespace(keyframe_points=[key(),key()]);layered=types.SimpleNamespace(keyframe_points=[key()]);bag=types.SimpleNamespace(fcurves=[layered]);strip=types.SimpleNamespace(channelbags=[bag]);layer=types.SimpleNamespace(strips=[strip]);action=types.SimpleNamespace(fcurves=[legacy],layers=[layer])
        self.assertEqual(linearize_action(action),3)
        self.assertTrue(all(k.interpolation=='LINEAR'for c in (legacy,layered)for k in c.keyframe_points))
        with self.assertRaises(ValueError):linearize_action(types.SimpleNamespace())

if __name__=='__main__':unittest.main()
