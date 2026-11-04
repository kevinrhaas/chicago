"""New binding admission composes preserved ancestors without retargeting them."""
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import generate_root_binding_v3 as generator

ROOT = Path(__file__).resolve().parent
APP = ROOT.parents[2]
STUDY = APP / 'assets/authored/transport/horse_standing'
MODE = 'natural_planted_root_binding_v3'
ORIGINAL925_SHA = '925fac957110b9b57b95c5abfed17fabf29f868b173f38f0569d984dd9999a48'
ORIGINAL_MOTION_SHA = '8ea7748ffba6c5fe17cde91042c6d8b26ed9a0ab77de69cadd4f4fb12e9c09fa'
CANDIDATE_SHA = '014ab3b117e0ab4462b41df7dde8c507ad58606eb461a1a8f2b9e89bc55fed63'
PAIRED_SHA = 'b1367d44c91bf2772110f6d1091c0cf4c2df85c8b74d5aba7f45ec50356c8716'
PHYSICAL_LOOP_SHA = 'a8515b35e18a058673fe330a127eba129851f324915858971e3b683bc4d259a1'
sha, need = generator.sha, generator.need

class Sources:
    def __init__(self):
        old_root = APP / 'tools/transport/horse_natural_idle_binding_v2'
        sys.path.insert(0, str(old_root))
        import binding_source as old
        self.prior_v2 = old.Sources()
        self.__dict__.update({k: v for k, v in self.prior_v2.__dict__.items() if k != 'raw'})
        self.raw = dict(self.prior_v2.raw)
        self.app, self.study = APP, STUDY
        self.binding_path = STUDY / 'horse-sevket-natural-planted-root-binding-v3.glb'
        self.paired_path = STUDY / 'horse-sevket-original925-root-binding-v3.glb'
        self.binding_recipe_path = STUDY / 'root-binding-v3-recipe.json'
        self.binding_recipe_raw = self.binding_recipe_path.read_bytes()
        self.binding_parent_raw = self.prior_v2.raw[self.prior_v2.binding_path]
        self.original925_raw = self.prior_v2.raw[self.prior_v2.paired_path]
        candidate, paired = self.binding_path.read_bytes(), self.paired_path.read_bytes()
        need(sha(candidate) == CANDIDATE_SHA and sha(paired) == PAIRED_SHA, 'exact newly versioned binding pair')
        self.overlay, _ = generator.binding(self.binding_parent_raw, self.binding_recipe_raw)
        self.structure = generator.inspect(self.binding_parent_raw, self.original925_raw,
                                           candidate, paired, self.binding_recipe_raw)
        self.byte_audit = generator.audit(self.binding_parent_raw, self.original925_raw, candidate,
                                     paired, self.binding_recipe_raw, self.overlay)
        for p in [self.binding_path, self.paired_path, self.binding_recipe_path,
                  ROOT / 'generate_root_binding_v3.py']:
            self.raw[p] = p.read_bytes()
        original = self.parent_mode.ancestor
        self.doc, self.binary = original.read_glb(candidate)
        self.body_positions, self.body_indices, self.body = original.mesh(self.doc, self.binary, 1)
        self.eye_positions, self.eye_indices, self.eye = original.mesh(self.doc, self.binary, 2)
        need(np.array_equal(self.body, self.prior_v2.body) and np.array_equal(self.eye, self.prior_v2.eye),
             'new binding has exactly the preserved candidate rest geometry')

    def cheap_tables(self):
        self.prior_v2.cheap_tables()
        return self.structure

    def unchanged(self):
        self.prior_v2.unchanged()
        for path, raw in self.raw.items():
            need(path.read_bytes() == raw, 'new binding or immutable ancestor input changed: ' + str(path))
        return True

def static(source):
    import socket_qualification as q
    import socket_geometry as geometry
    source.cheap_tables()
    components = q.components(source, source.eye)
    allowed, ledger = q.source_interface_faces(source, components)
    for side, component in components.items():
        geometry.need(not q.proper_pairs(component.triangles, set(range(len(component.triangles))), source.crosses),
                      'source_globe_self_intersection', side)
    baseline = {j for i, j in q.globe_pairs(source.old_body, set(range(len(source.old_body))), source.eye, source.crosses)}
    rest = q.evaluate_frame(source, source.body, source.old_body, source.eye, source.eye,
                            allowed, {'kind': 'rest'}, baseline)
    source.unchanged()
    return {'status': 'ROOT_BINDING_V3_CURRENT_SOURCE_STATIC_ONLY_PASS', 'source_admission': MODE,
            'candidate_sha256': CANDIDATE_SHA, 'paired925_sha256': PAIRED_SHA,
            'immutable_original925_sha256': ORIGINAL925_SHA,
            'immutable_motion_source_sha256': ORIGINAL_MOTION_SHA,
            'recipe_sha256': sha(source.binding_recipe_raw), 'structure': source.structure,
            'byte_domain': source.byte_audit, 'rest': rest,
            'source_interface_faces': {str(k): sorted(v) for k, v in allowed.items()},
            'source_interface_ledger': ledger, 'old13_native129': 'UNRUN',
            'new17_physical129': 'UNRUN', 'paired925_socket129': 'UNRUN',
            'old_certificate_transferred': False, 'runtime_adoption': False}
