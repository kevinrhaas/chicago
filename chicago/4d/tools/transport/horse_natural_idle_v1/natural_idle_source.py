"""First-class new motion child of exact bd443; no old verdict is inherited."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parent
APP = ROOT.parents[2]
STUDY = APP / 'assets/authored/transport/horse_standing'
MODE = 'natural_planted_idle_v1'
PARENT_SHA = 'bd443df87b92d19266284cb9b52d30e791215cddf099876c774e9cfb5f5a79b6'
CANDIDATE_SHA = '8ea7748ffba6c5fe17cde91042c6d8b26ed9a0ab77de69cadd4f4fb12e9c09fa'
RECIPE_SHA = 'f948df0e0dc510475df1de85ba5954f46c1b4035f041df582265a37a4ff4b1ef'
PHYSICAL_LOOP_SHA = 'a8515b35e18a058673fe330a127eba129851f324915858971e3b683bc4d259a1'
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Sources:
    def __init__(self):
        sys.path.insert(0, str(APP / 'tools/transport/horse_eye_smooth_normals_v1'))
        import normal_child_source as normal
        self.normal = normal.Sources(APP, STUDY)
        self.__dict__.update({key: value for key, value in self.normal.__dict__.items()
                              if key not in ('app', 'study')})
        self.app, self.study = APP, STUDY
        self.raw = dict(self.normal.raw)
        self.motion_path = STUDY / 'horse-sevket-natural-planted-idle-v1.glb'
        self.motion_recipe_path = STUDY / 'natural-planted-idle-v1-recipe.json'
        self.motion_generator_path = STUDY / 'generate_natural_planted_idle_v1.py'
        self.expected_path = ROOT / 'independent-natural-idle65-matrices.json'
        for path in (self.motion_path, self.motion_recipe_path, self.motion_generator_path,
                     self.expected_path, ROOT / 'expected_matrices.py'):
            self.raw[path] = path.read_bytes()
        parent = self.normal.raw[self.normal.child_path]
        candidate = self.raw[self.motion_path]
        recipe_raw = self.raw[self.motion_recipe_path]
        need(sha(parent) == PARENT_SHA and sha(candidate) == CANDIDATE_SHA,
             'explicit exact bd443 parent and new8ea motion candidate')
        need(sha(recipe_raw) == RECIPE_SHA, 'exact reviewed reconstructed motion recipe')
        self.motion_generator = load_module(self.motion_generator_path, 'canonical_natural_idle_generator')
        self.expected_generator = load_module(ROOT / 'expected_matrices.py', 'canonical_natural_idle_expected_matrices')
        self.motion_recipe = json.loads(recipe_raw)
        self.motion_structure = self.motion_generator.inspect(parent, candidate, recipe_raw)
        need(self.motion_generator.derive(parent, recipe_raw) == candidate, 'exact portable motion regeneration')
        need(json.loads(self.raw[self.expected_path]) == self.expected_generator.generate(),
             'independent expected65 Euler/hierarchy input regeneration')
        self.motion_parent_raw = parent
        self.doc, self.binary = self.parent_mode.ancestor.read_glb(candidate)
        ancestor = self.parent_mode.ancestor
        self.body_positions, self.body_indices, self.body = ancestor.mesh(self.doc, self.binary, 1)
        self.eye_positions, self.eye_indices, self.eye = ancestor.mesh(self.doc, self.binary, 2)
        need(np.array_equal(self.body, self.normal.body) and np.array_equal(self.eye, self.normal.eye),
             'new motion cannot change rest BODY or immutable globe geometry')

    def cheap_tables(self):
        self.normal.cheap_tables()
        self.motion_generator.inspect(self.motion_parent_raw, self.raw[self.motion_path],
                                      self.raw[self.motion_recipe_path])
        return self.motion_structure

    def full_frozen_structure(self):
        return {'source_admission': MODE,
                'normal_parent_exact_bd443': self.normal.full_frozen_structure(),
                'new_animation_only_structure': self.motion_structure,
                'selected_exported_clip_index': 1,
                'selected_exported_clip': 'sevket_reconstructed_natural_planted_idle_v1',
                'selected_exported_track_count': 17,
                'old_certificate_transferred': False, 'new_actual_native129': 'REQUIRED_UNRUN'}

    def unchanged(self):
        self.normal.unchanged()
        for path, raw in self.raw.items():
            need(path.read_bytes() == raw, 'protected new motion proof input changed: ' + str(path))
        return True


def source_controls(source):
    generator = source.motion_generator
    candidate = source.raw[source.motion_path]
    parent = source.motion_parent_raw
    recipe = source.raw[source.motion_recipe_path]
    doc, binary = generator.read_glb(candidate)
    _, old_binary = generator.read_glb(parent)
    checks = []

    def refused(name, bad):
        try:
            generator.inspect(parent, bad, recipe)
        except (ValueError, KeyError, IndexError):
            checks.append(name)
            return
        raise AssertionError('meaningful source corruption accepted: ' + name)

    def changed_doc(name, change):
        bad = copy.deepcopy(doc)
        change(bad)
        refused(name, generator.write_glb(bad, binary))

    damaged = bytearray(binary)
    damaged[len(old_binary) + 76] ^= 64
    refused('new_quaternion_stream_changed', generator.write_glb(doc, bytes(damaged)))
    damaged = bytearray(binary)
    damaged[17] ^= 1
    refused('parent_BIN_byte_changed', generator.write_glb(doc, bytes(damaged)))
    changed_doc('new_target_body_instead_of_neck', lambda d: d['animations'][1]['channels'][13]['target'].update(node=1))
    changed_doc('new_output_out_of_bounds', lambda d: d['bufferViews'][-1].update(byteOffset=1000000000))
    changed_doc('new_interpolation_changed', lambda d: d['animations'][1]['samplers'][13].update(interpolation='STEP'))
    changed_doc('new_time_accessor_changed', lambda d: d['animations'][1]['samplers'][13].update(input=0))
    changed_doc('new_output_accessor_changed', lambda d: d['animations'][1]['samplers'][13].update(output=0))
    changed_doc('new_output_count_changed', lambda d: d['accessors'][-1].update(count=64))
    changed_doc('parent_author_changed', lambda d: d['asset']['extras'].update(author='Changed original author'))
    changed_doc('old_clip_changed', lambda d: d['animations'][0].update(name='Different retained old clip'))
    changed_doc('parent_node_rest_changed', lambda d: d['nodes'][2].update(translation=[0, 0, 0]))
    changed_doc('unlisted_metadata_added', lambda d: d.update(unreviewed_field=True))
    need(len(checks) == 12, 'all twelve meaningful new source controls executed')
    return checks


def static(source):
    import socket_qualification as q
    import socket_geometry as g
    original = source.parent_mode.ancestor
    source.cheap_tables()
    components = q.components(source, source.eye)
    allowed, ledger = q.source_interface_faces(source, components)
    for side, component in components.items():
        g.need(not q.proper_pairs(component.triangles, set(range(len(component.triangles))), source.crosses),
               'source_globe_self_intersection', side)
    baseline = {j for i, j in q.globe_pairs(source.old_body, set(range(len(source.old_body))), source.eye, source.crosses)}
    rest = q.evaluate_frame(source, source.body, source.old_body, source.eye, source.eye,
                            allowed, {'kind': 'rest'}, baseline)
    source.unchanged()
    return {'status': 'NATURAL_IDLE_CURRENT_SOURCE_STATIC_ONLY_PASS', 'source_admission': MODE,
            'candidate_sha256': CANDIDATE_SHA, 'motion_parent_bd443_sha256': PARENT_SHA,
            'collision_reference925_sha256': original.EXPECTED[original.PARENT],
            'recipe_sha256': RECIPE_SHA, 'collision_mode': original.MODE,
            'structure': source.full_frozen_structure(), 'rest': rest,
            'source_interface_faces': {str(k): sorted(v) for k, v in allowed.items()},
            'source_interface_ledger': ledger, 'physical129': 'UNRUN', 'posed129': 'UNRUN',
            'old_certificate_transferred': False, 'source_adoption': False, 'photographic_acceptance': False}
