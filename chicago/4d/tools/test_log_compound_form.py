#!/usr/bin/env python3
"""T-2374: bounded room eaves and ridge-stack opt-ins, no Blender required."""
import copy
import dataclasses
import json
import math
import sys
import types
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'generators'))
sys.modules.setdefault('bpy',types.ModuleType('bpy'))
from archetypes import log_dwelling as builder
from archetypes.log_dwelling_params import from_phase, ParamError, compound_gable_face
from common.mesh import MeshBuilder

def current():
    rec=json.loads((ROOT/'data/structures/cobweb_castle.json').read_text())
    return from_phase(rec['phases'][0],rec)

class CompoundForm(unittest.TestCase):
    def test_defaults_remain_keyword_only_and_off(self):
        fields={f.name:f for f in dataclasses.fields(current())}
        for name in ('compound_eave_heights_m','compound_ridge_stacks'):
            self.assertTrue(fields[name].kw_only)
            self.assertIsNone(fields[name].default)

    def test_refuses_unsupported_or_impossible_setouts(self):
        p=current()
        cases=[{'chimney_head_m':4.4}, {'compound_eave_heights_m':()}, {'compound_eave_heights_m':(2.6,)*4},
               {'compound_eave_heights_m':(2.6,True,2,2.6,2.6)},
               {'compound_eave_heights_m':(2.6,math.nan,2,2.6,2.6)},
               {'compound_eave_heights_m':(2.6,1.7,2,2.6,2.6)},
               {'compound_clapboard_height_m':1.9},
               {'compound_ridge_stacks':()}, {'compound_ridge_stacks':((True,.5,.8),)},
               {'compound_ridge_stacks':((99,.5,.8),)},
               {'compound_ridge_stacks':((0,math.inf,.8),)},
               {'compound_ridge_stacks':((0,.5,True),)},
               {'compound_ridge_stacks':((0,.01,.8),)},
               {'compound_ridge_stacks':((0,.05,1.2),)},
               {'compound_ridge_stacks':((0,.5,.2),)},
               {'chimneys':2,'compound_ridge_stacks':((0,.5,.8),(0,.51,.8))}]
        for change in cases:
            with self.subTest(change=change),self.assertRaises(ParamError):
                dataclasses.replace(p,**change).validate()
        rec=json.loads((ROOT/'data/structures/walker_meeting_house.json').read_text())
        plain=from_phase(rec['phases'][0],rec)
        for change in ({'compound_ridge_stacks':((0,.5,.8),)}, {'compound_eave_heights_m':(2.6,)}):
            with self.assertRaises(ParamError):dataclasses.replace(plain,**change).validate()

    def test_emitted_stack_is_on_its_own_roof_and_one_only(self):
        p=dataclasses.replace(current(),compound_clapboard_height_m=None)
        before,after=MeshBuilder('cobweb_castle__log_1820'),MeshBuilder('cobweb_castle__log_1820')
        builder._compound(before,dataclasses.replace(p,chimneys=0,compound_ridge_stacks=None))
        builder._compound(after,p)
        self.assertEqual(after.verts[:len(before.verts)],before.verts)
        self.assertEqual(after.faces[:len(before.faces)],before.faces)
        stack=after.verts[len(before.verts):]
        self.assertEqual(len(stack),20)  # one five-faced shaft, no ground-reaching exterior stack
        expected=((4.1,1.825,compound_gable_face(p,0)[5]-.4*math.tan(math.radians(35))-.25),
                  (4.9,2.625,5.05))
        for axis in range(3):
            self.assertAlmostEqual(min(v[axis] for v in stack),expected[0][axis])
            self.assertAlmostEqual(max(v[axis] for v in stack),expected[1][axis])
        self.assertEqual(compound_gable_face(p,0)[4],2.6)
        self.assertEqual(compound_gable_face(p,1)[4],2.0)
        self.assertLess(compound_gable_face(p,1)[5],compound_gable_face(p,0)[4]+.3)

if __name__=='__main__':unittest.main()
