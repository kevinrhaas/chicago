"""Tiny posed-unsafe fixture through actual production129 traversal, no horse run."""
import argparse,copy,json,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import socket_geometry as g
import socket_sources as s
import socket_qualification as q
from socket_controls import box

def run(out):
 started=time.monotonic();g.need(not out.exists(),'fresh_control_output_required');bound=s.Sources();bound.cheap_tables()
 component=g.ClosedComponent(box([.06,-.04,-.04],[.14,.04,.04]),1,'tiny traversal control globe')
 other=np.array([[.04,-.08,0],[.18,-.08,0],[.11,.08,0]])
 patch=np.array([[.1399995,0,-.01],[.1399995,0,.01],[2*.1399997-.1399995,0,.01]])
 assert bound.crosses(patch,other)and bound.crosses(other,patch)
 reference=g.intersection_segment(patch,other);assert component.contained(reference)
 identity=[int(i%5==0)for i in range(16)];source=SimpleNamespace(body_indices=np.array([[0,1,2]]),old_indices=np.array([[0,1,2]]),eye_indices=np.array([[0,1,2]]))
 def inventory(unsafe=False):
  rows=[];physical=[]
  for i in range(129):
   matrix=[identity.copy()for _ in range(26)]
   if i==37:matrix[2][12]=.2
   nodes=[[0.0]*26 for _ in range(29)];nodes[2][0]=.2 if i==37 else 0
   row={'index':i,'time_s':i*3/32,'key':i//2 if i%2==0 else None,'bone_states_identical':True,'skeletons_updated':True,'mesh_bind_bases_identity':True,'candidate_node_states':copy.deepcopy(nodes),'parent_node_states':copy.deepcopy(nodes),'candidate_skeleton_matrices':[[0.0]*(26*16)for _ in range(3)],'parent_skeleton_matrices':[[0.0]*(26*16)for _ in range(3)],'actual_mesh_bind_bases':[[identity.copy()for _ in range(3)]for _ in range(4)],'candidate_bone_world_matrices':copy.deepcopy(matrix),'parent_bone_world_matrices':copy.deepcopy(matrix)}
   moved=patch.copy()
   if unsafe and i==37:moved[:,0]+=6.5e-6*.2
   for key in('candidate_body','parent_body','candidate_eye','parent_eye'):row[key]={'values':moved.copy()if key=='candidate_body'else patch.copy()}
   rows.append(row);physical.append({'time':row['time_s'],'key':row['key'],'world_matrices':copy.deepcopy(matrix)})
  return rows,physical
 visited=[]
 def reader(base,row,shape):return row['values']
 def actual_fixture_evaluator(source,body,parent,eye,parent_eye,allowed,frame,baseline):
  visited.append(frame['index']);assert bound.crosses(body[0],other)and bound.crosses(other,body[0]);segment=g.intersection_segment(body[0],other)
  return g.admit_body_crossing(segment,1,7,other,other,component,{7},[reference])
 frames,physical=inventory();safe=q.traverse_pose_frames(source,frames,Path('/tmp'),{1:{7}},set(),physical,array_reader=reader,frame_evaluator=actual_fixture_evaluator)
 assert len(safe)==129 and visited==list(range(129));visited.clear()
 frames,physical=inventory(unsafe=True)
 try:q.traverse_pose_frames(source,frames,Path('/tmp'),{1:{7}},set(),physical,array_reader=reader,frame_evaluator=actual_fixture_evaluator)
 except g.Rejected as error:assert error.code=='exterior_segment_endpoint';actual_error=error.code
 else:raise AssertionError('Actual nonrest geometric corruption incorrectly accepted')
 assert visited==list(range(38))and visited[-1]==37
 bound.unchanged()
 result={'status':'FOCUSED_PRODUCTION129_TRAVERSAL_CONTROL_ONLY_PASS','code_pins':q.code_pins(),'positive_fixture_actual_visited':129,'negative_fixture_actual_visited':visited,'actual_rejection':actual_error,'unsafe_index':37,'unsafe_time_s':37*3/32,'unsafe_key':None,'rest_safe':True,'both_crossings_proper_with_pinned_kernel':True,'neck_weight':6.5e-6,'relative_neck_translation_m':.2,'relative_shift_m':1.3e-6,'method':'Actual production traversal with tiny fixture array reader and exact same containment/admission predicates; safe129 and one truly posed-unsafe sample37. No horse mesh/native browser capture was run.','seconds':time.monotonic()-started,'full_horse_static':'UNRUN','native129_capture':'UNRUN','native129_interface':'UNRUN','source_adoption':False,'photographic_acceptance':False}
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'positive_samples':129,'unsafe_sample':37,'seconds':result['seconds']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out)
