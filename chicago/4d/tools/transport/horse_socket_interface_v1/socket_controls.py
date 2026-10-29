"""Focused real geometric/source-table controls, not full horse qualification."""
import copy,hashlib,json,math,time
from pathlib import Path
import numpy as np
import socket_geometry as g
import socket_sources as s

def box(lo,hi):
    a,b,c=lo;x,y,z=hi
    v=np.array([[a,b,c],[x,b,c],[x,y,c],[a,y,c],[a,b,z],[x,b,z],[x,y,z],[a,y,z]],dtype=float)
    f=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]
    return v[np.array(f)]

def notch():
    # CCW polygon: off-centre top notch. Endpoint AND midpoint-only checks fail.
    p=np.array([[0,0],[4,0],[4,2],[1.5,2],[1.5,.5],[.5,.5],[.5,2],[0,2]],float)
    def orient(a,b,c):return float(np.cross(b-a,c-a))
    ring=list(range(len(p)));cap=[]
    while len(ring)>3:
        for k,i in enumerate(ring):
            a,b=ring[k-1],ring[(k+1)%len(ring)]
            if orient(p[a],p[i],p[b])<=0:continue
            inside=False
            for j in ring:
                if j in(a,i,b):continue
                if min(orient(p[a],p[i],p[j]),orient(p[i],p[b],p[j]),orient(p[b],p[a],p[j]))>=0:inside=True;break
            if inside:continue
            cap.append((a,i,b));ring.pop(k);break
        else:raise AssertionError('Fixture polygon ear clipping failed')
    cap.append(tuple(ring));v=np.vstack([np.column_stack([p,np.full(len(p),-.5)]),np.column_stack([p,np.full(len(p),.5)])]);faces=[]
    for a,b,c in cap:faces.extend([(a,c,b),(a+8,b+8,c+8)])
    for a in range(8):b=(a+1)%8;faces.extend([(a,b,b+8),(a,b+8,a+8)])
    return v[np.array(faces)]

def run(out):
    started=time.monotonic();source=s.Sources();results={}
    def ok(name,fn):
        value=fn();results[name]={'passed':True,'actual':value};return value
    def refused(name,code,fn):
        try:fn()
        except g.Rejected as error:
            assert error.code==code,(name,error.code,code);results[name]={'refused':True,'specific_reason':error.code,'detail':str(error)}
        else:raise AssertionError('Control unexpectedly accepted: '+name)
    positive=g.ClosedComponent(box([.06,-.04,-.04],[.14,.04,.04]),1,'positive fixture')
    negative=g.ClosedComponent(box([-.14,-.04,-.04],[-.06,.04,.04]),-1,'negative fixture')
    other=np.array([[.04,-.08,0],[.18,-.08,0],[.11,.08,0]])
    def patch(x0,x1):return np.array([[x0,0,-.01],[x0,0,.01],[2*x1-x0,0,.01]])
    def proper(a,b):
        assert source.crosses(a,b)and source.crosses(b,a),'Focused control lacks a genuine proper crossing'
        return g.intersection_segment(a,b)
    good=proper(patch(.099,.101),other)
    ok('contained_proper_interface_positive',lambda:g.admit_body_crossing(good,1,7,other,other,positive,{7},[good]))
    exterior=proper(patch(.13,.143),other)
    refused('proper_exterior_crossing', 'exterior_segment_endpoint',lambda:g.admit_body_crossing(exterior,1,7,other,other,positive,{7},[good]))
    refused('wrong_side_even_inside_other_globe','wrong_side_component',lambda:g.admit_body_crossing(good,-1,7,other,other,positive,{7},[good]))
    refused('undeclared_unchanged_face_inside_globe','undeclared_original_interface_face',lambda:g.admit_body_crossing(good,1,999,other,other,positive,{7},[good]))
    changed=other.copy();changed[0,2]+=1e-6;changed_locus=proper(patch(.099,.101),changed)
    refused('changed_source_interface_face','changed_original_interface_face',lambda:g.admit_body_crossing(changed_locus,1,7,changed,other,positive,{7},[good]))
    refused('patch_patch_even_buried','patch_patch_crossing_forbidden',lambda:g.admit_body_crossing(good,1,7,other,other,positive,{7},[good],both_replaced=True))
    long=proper(patch(.099,.12),other)
    assert positive.contained(long)
    refused('small_minimum_but_far_locus_exceeds14mm','whole_locus_distance_limit',lambda:g.admit_body_crossing(long,1,7,other,other,positive,{7},[good]))
    # Pretending the old slot/pair was inherited cannot reach an acceptance path.
    refused('fake_old_pair_does_not_excuse_exterior','exterior_segment_endpoint',lambda:g.admit_body_crossing(exterior,1,7,other,other,positive,{7},[good]))
    u=g.ClosedComponent(notch(),1,'off-centre nonconvex fixture')
    ta=np.array([[-1,-1,0],[5,-1,0],[2,4,0]],float);tb=np.array([[-1.5,1,-1],[5.5,1,-1],[2,1,1]],float);cut=proper(ta,tb)
    assert u.location(cut.a)=='INSIDE'and u.location(cut.b)=='INSIDE'and u.location(cut.point(g.Q(1,2)))=='INSIDE'
    assert u.location(cut.point(g.Q(1,4)))=='OUTSIDE'
    refused('endpoints_and_midpoint_inside_but_offcentre_interval_outside','exterior_segment_interval',lambda:g.admit_body_crossing(cut,1,7,ta,ta,u,{7},[cut]))
    results['nonconvex_exact_events']={'events':[str(x)for x in u.segment_events(cut)],'expected_exterior_interval':['1/14','5/14']}
    # No near-surface ray entry is skipped. This point is >1nm outside.
    q=[.14+3e-9,0,0];ok('three_nanometres_outside_is_not_inside',lambda:{'location':positive.location(q)})
    assert positive.location(q)=='OUTSIDE'
    refused('no_3nm_volume_padding','exterior_segment_endpoint',lambda:positive.contained(g.Segment(q,[.15,0,0])))
    # Same geometry at rest is safe, but tiny nonzero neck influence moves it out.
    near=proper(patch(.1399995,.1399997),other);assert positive.contained(near)
    posed=g.Segment(np.array([float(x)for x in near.a])+[1.3e-6,0,0],np.array([float(x)for x in near.b])+[1.3e-6,0,0])
    refused('rest_safe_but_nonrest_exterior','exterior_segment_endpoint',lambda:g.admit_body_crossing(posed,1,7,other,other,positive,{7},[near]))
    results['posed_control_relationship']={'neck_weight':6.5e-6,'relative_neck_translation_m':.2,'actual_relative_shift_m':1.3e-6,'rest_contained':True,'posed_rejected':True,'scope':'Focused pose-dependent predicate fixture, not actual129 execution.'}
    globe_face=6;globe_tri=positive.triangles[globe_face]
    contact_body=np.array([[.13,0,0],[.15,0,0],[.14,.002,0]])
    contact=proper(contact_body,globe_tri)
    ok('proper_same_side_surface_contact_positive',lambda:g.admit_globe_contact(contact,1,positive,[contact],globe_face))
    far_body=np.array([[.13,0,0],[.15,0,0],[.14,.035,0]]);far=proper(far_body,globe_tri)
    refused('surface_locus_exceeds7mm','whole_locus_distance_limit',lambda:g.admit_globe_contact(far,1,positive,[contact],globe_face))
    refused('wrong_side_surface_contact','wrong_side_globe_contact',lambda:g.admit_globe_contact(contact,-1,positive,[contact],globe_face))
    refused('wrong_component_face_identity','undeclared_globe_component_face',lambda:g.admit_globe_contact(contact,1,positive,[contact],999))
    interior=g.Segment([.099,0,0],[.101,0,0])
    refused('claimed_contact_not_on_attested_surface','contact_not_on_attested_globe_face',lambda:g.admit_globe_contact(interior,1,positive,[interior],globe_face))
    flat=g.Segment([.14,0,0],[.14,.001,0])
    refused('coplanar_containment_fails_closed','coplanar_segment_surface_contact_not_supported',lambda:positive.contained(flat))
    refused('open_component_refused','component_not_closed_or_oriented',lambda:g.ClosedComponent(positive.triangles[:-1],1,'open'))
    reversed_faces=positive.triangles.copy();reversed_faces[0]=reversed_faces[0,::-1]
    refused('reversed_component_face_refused','component_not_closed_or_oriented',lambda:g.ClosedComponent(reversed_faces,1,'reversed'))
    ok('actual_bound_source_UV_skin_tables',source.cheap_tables)
    p=source.doc['meshes'][1]['primitives'][0];attrs=p['attributes'];eye=source.doc['meshes'][2]['primitives'][0]
    def mutate(accessor,row):
        b=bytearray(source.binary);b[s.byte_offset(source.doc,accessor,row)]^=1;return b
    for name,index,row,code in [('third_BODY_UV',attrs['TEXCOORD_0'],0,'undeclared_BODY_UV_mutation'),('wrong_declared_BODY_UV',attrs['TEXCOORD_0'],2410,'wrong_declared_BODY_UV_repair'),('BODY_skin',attrs['WEIGHTS_0'],414,'BODY_skin_mutation'),('EYE_UV',eye['attributes']['TEXCOORD_0'],0,'globe_TEXCOORD_0_mutation'),('globe_position',eye['attributes']['POSITION'],0,'globe_POSITION_mutation')]:
        altered=mutate(index,row)
        refused(name,code,lambda b=altered:s.uv_skin_guard(source.doc,b,source.parent_doc,source.parent_bin,source.recipe))
    alias=copy.deepcopy(source.doc);alias['meshes'][1]['primitives'][0]['attributes']['TEXCOORD_1']=attrs['POSITION']
    refused('BODY_UV_alias_mutation','BODY_UV_alias_divergence',lambda:s.uv_skin_guard(alias,source.binary,source.parent_doc,source.parent_bin,source.recipe))
    rig=copy.deepcopy(source.doc);rig['nodes'][0]['name']+=' changed'
    refused('rig_structure_mutation','rig_or_skin_structure_mutation',lambda:s.uv_skin_guard(rig,source.binary,source.parent_doc,source.parent_bin,source.recipe))
    prefix=bytearray(source.binary);prefix[0]^=1
    refused('original_BIN_prefix_mutation','original_d454_BIN_prefix_mutation',lambda:s.original_prefix_guard(prefix,source.original_bin))
    source.unchanged()
    result={'schema':'canonical_socket_interface_focused_controls_v1','status':'FOCUSED_CONTROLS_ONLY_PASS','source_hashes':{str(p):h for p,h in s.EXPECTED.items()},'results':results,'seconds':time.monotonic()-started,'full_horse_static_qualification':'UNRUN','native129_interface':'UNRUN','original_mode_files_changed':False,'source_adoption':False,'photographic_acceptance':False,'scope':'Tiny geometric fixtures and actual UV/skin source-table controls; no full horse intersection census, frozen topology inspection, native browser or qualification verdict.'}
    need_path=Path(out);assert not need_path.exists();need_path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'controls':len(results),'seconds':result['seconds'],'out':str(need_path)}))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);run(p.parse_args().out)
