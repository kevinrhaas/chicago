"""PROPOSED first-class exact V4HEAD replay. Outside app; canonical phases UNRUN."""
from pathlib import Path
import copy,json
import numpy as np
import generate_quiet_head_neck_v6 as producer

ROOT=Path(__file__).resolve().parent
APP=ROOT.parents[2]
FIELD_SHA='3b4c315155ba3ecb3250d345e15179f6ad7ca673de2ae7a999625fdabaa5532f'
MASTER_SHA='0a93029a951c000771c9fc8ca39809fd5323633b2e70fc462ba27b7ab9ccfc5b'
PAIR_SHA='fd3cd0bdf928551b21837442fc4d3e4d5008208cadd4cb832ec54565b1b95775'
sha,need=producer.sha,producer.need

def exact_head_template(parent,field_raw):
    need(sha(parent)==producer.PARENT and sha(field_raw)==FIELD_SHA,'immutable V2 and exact authored V4HEAD field')
    spec=json.loads(field_raw);doc,binary=producer.read(parent)
    need(spec['source_V2_parent_sha256']==producer.PARENT and spec['source_V4_unqualified_fullcandidate_sha256']==producer.HEAD,'explicit unqualified V4 lineage, HEAD field only')
    pos=producer.view(doc,binary,0,'POSITION')[0]
    rows=np.flatnonzero((pos[:,1]>1.04)&(pos[:,2]>.28))
    need(rows.tolist()==spec['head_rows'] and len(rows)==2306 and sha(pos.tobytes())==spec['source_HAIR_POSITION_sha256'],'source-bound HEAD row identities')
    changes=spec['field_rows'];need(len(changes)==417 and len({r['row'] for r in changes})==417,'all417 unique authored HEAD changes')
    allowed=set(rows.tolist());out=bytearray(binary)
    for semantic,key in [('JOINTS_0','joints'),('WEIGHTS_0','weights')]:
        a,start,stride,width=producer.view(doc,binary,0,semantic)
        for r in changes:
            need(r['row'] in allowed,'HEAD-only source field')
            value=np.asarray(r[key],dtype=a.dtype);need(value.shape==(4,),'four-component tuple')
            offset=start+r['row']*stride;out[offset:offset+width]=value.tobytes()
    result=producer.write(doc,out);rd,rb=producer.read(result)
    actual=producer.view(rd,rb,0,'JOINTS_0')[0][rows].tobytes()+producer.view(rd,rb,0,'WEIGHTS_0')[0][rows].tobytes()
    need(sha(actual)==spec['full2306_HEAD_JOINTS_then_WEIGHTS_sha256'],'all2306 HEAD tuples exact V4')
    return result

def replay(parent,reference,field_raw,recipe):
    need(sha(parent)==producer.PARENT and sha(reference)==producer.PAIR,'actual immutable V2 candidate/pair')
    head=exact_head_template(parent,field_raw)
    master=producer.export(parent,head,sha(recipe),producer.PARENT,'quiet15-candidate')
    paired=producer.export(reference,head,sha(recipe),producer.PAIR,'paired925-head-neck-reference')
    need(sha(master)==MASTER_SHA and sha(paired)==PAIR_SHA,'byte-exact already-authored V6 candidate/pair; no new asset version or tuning')
    admission=producer.pair_admission(parent,reference,master,paired,head,sha(recipe))
    return master,paired,admission
