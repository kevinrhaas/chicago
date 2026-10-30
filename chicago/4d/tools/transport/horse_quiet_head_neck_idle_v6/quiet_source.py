"""PROPOSED first-class V6 source/static adapter. Never transfers an old verdict."""
from pathlib import Path
import sys,json
import numpy as np
import head_field_source as head
import runtime_projection
ROOT=Path(__file__).resolve().parent
APP=ROOT.parents[2]
MODE='quiet_head_neck_idle_v6'
MASTER_SHA=head.MASTER_SHA
CANDIDATE_SHA='7ce84d43445e930eecc6d9f69e97ed7ade0fe0b3fc44a9a753c25d88b3f548e1'
PAIRED_SHA=head.PAIR_SHA
PHYSICAL_LOOP_SHA='a8515b35e18a058673fe330a127eba129851f324915858971e3b683bc4d259a1'
ORIGINAL925_SHA='925fac957110b9b57b95c5abfed17fabf29f868b173f38f0569d984dd9999a48'
ORIGINAL_MOTION_SHA='8ea7748ffba6c5fe17cde91042c6d8b26ed9a0ab77de69cadd4f4fb12e9c09fa'
sha,need=head.sha,head.need

class Sources:
    def __init__(self):
        sys.path.insert(0,str(APP/'tools/transport/horse_natural_idle_binding_v2'))
        import binding_source as old
        self.prior_v2=old.Sources()
        self.__dict__.update({k:v for k,v in self.prior_v2.__dict__.items() if k!='raw'})
        self.raw=dict(self.prior_v2.raw)
        audit=json.loads((ROOT/'INPUTS.json').read_bytes());new={}
        for name,row in audit['inputs'].items():
            p=APP/row['path'];raw=p.read_bytes()
            need(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'exact first-class input '+name)
            self.raw[p]=raw;new[name]=raw
        self.master_path=APP/audit['inputs']['candidate']['path'];self.binding_path=APP/audit['inputs']['runtime_candidate']['path'];self.paired_path=APP/audit['inputs']['paired_reference']['path']
        self.binding_recipe_raw=new['quiet_recipe'];self.binding_parent_raw=new['v2_candidate'];self.original925_raw=new['v2_paired_reference']
        self.master_raw,self.paired_raw,replay=head.replay(self.binding_parent_raw,self.original925_raw,new['head_field'],self.binding_recipe_raw)
        need(self.master_raw==new['candidate'] and self.paired_raw==new['paired_reference'],'actual staged master/pair equal exact independent source replay')
        projection=runtime_projection.inspect(self.master_raw,new['runtime_candidate'])
        need(projection['runtime_sha256']==CANDIDATE_SHA,'exact separately versioned one-clip runtime')
        self.structure=dict(master_source_admission=replay,runtime_projection=projection)
        original=self.parent_mode.ancestor
        self.doc,self.binary=original.read_glb(new['runtime_candidate'])
        self.body_positions,self.body_indices,self.body=original.mesh(self.doc,self.binary,1)
        self.eye_positions,self.eye_indices,self.eye=original.mesh(self.doc,self.binary,2)
        need(np.array_equal(self.body,self.prior_v2.body) and np.array_equal(self.eye,self.prior_v2.eye),'complete protected BODY/EYE rest geometry exact')
        for p in [ROOT/'head_field_source.py',ROOT/'generate_quiet_head_neck_v6.py',ROOT/'runtime_projection.py',ROOT/'quiet_source.py',ROOT/'INPUTS.json']:
            self.raw[p]=p.read_bytes()

    def cheap_tables(self):
        self.prior_v2.cheap_tables()
        return self.structure

    def unchanged(self):
        self.prior_v2.unchanged()
        for path,raw in self.raw.items():need(path.read_bytes()==raw,'new or ancestor source changed '+str(path))
        return True

def static(source):
    import socket_qualification as q
    import socket_geometry as g
    source.cheap_tables();components=q.components(source,source.eye);allowed,ledger=q.source_interface_faces(source,components)
    for side,component in components.items():
        g.need(not q.proper_pairs(component.triangles,set(range(len(component.triangles))),source.crosses),'source_globe_self_intersection',side)
    baseline={j for i,j in q.globe_pairs(source.old_body,set(range(len(source.old_body))),source.eye,source.crosses)}
    rest=q.evaluate_frame(source,source.body,source.old_body,source.eye,source.eye,allowed,{'kind':'rest'},baseline)
    source.unchanged()
    return dict(status='QUIET_HEAD_NECK_V6_CURRENT_SOURCE_STATIC_ONLY_PASS',source_admission=MODE,authored_master_sha256=MASTER_SHA,runtime_candidate_sha256=CANDIDATE_SHA,paired925_sha256=PAIRED_SHA,immutable_original925_sha256=ORIGINAL925_SHA,immutable_motion_source_sha256=ORIGINAL_MOTION_SHA,recipe_sha256=sha(source.binding_recipe_raw),structure=source.structure,rest=rest,source_interface_faces={str(k):sorted(v) for k,v in allowed.items()},source_interface_ledger=ledger,old13_native129='UNRUN',master_quiet15_physical129='UNRUN',runtime_quiet15_physical129='UNRUN',runtime_master_parity129='UNRUN',paired925_socket129='UNRUN',old_certificate_transferred=False,runtime_adoption=False)
