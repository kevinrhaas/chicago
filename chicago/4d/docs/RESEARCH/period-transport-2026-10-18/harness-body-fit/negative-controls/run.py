from pathlib import Path
import tempfile,shutil,struct,json,gzip,hashlib,subprocess,sys
O=Path(__file__).parent;R=Path('/workspace/chicago/chicago/4d');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();tool=R/'tools/transport/test_harness_body_fit.py';horse=R/'renderers/web/transport/horse/equine_light_harness_skinned_prototype_01.glb';gear=R/'renderers/web/transport/harness/light_breastcollar_harness_reconstructed_01.glb';archive=R/'tools/transport/fixtures/harness-before-body-fit.glb.gz';raw=gear.read_bytes();n=struct.unpack_from('<I',raw,12)[0];base=json.loads(raw[20:20+n]);binary=raw[28+n:];results=[]
def packed(g):
 j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);return struct.pack('<III',0x46546c67,2,28+len(j)+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
for case in ['removed_mesh','renamed_part','orphaned_part','original_as_candidate']:
 with tempfile.TemporaryDirectory(prefix='harness-negative-',dir='/tmp')as temporary:
  root=Path(temporary)
  for src,dest in [(tool,'tools/transport/test_harness_body_fit.py'),(horse,'renderers/web/transport/horse/equine_light_harness_skinned_prototype_01.glb'),(archive,'tools/transport/fixtures/harness-before-body-fit.glb.gz')]:
   path=root/dest;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,path)
  g=json.loads(json.dumps(base));nodeid=next(i for i,node in enumerate(g['nodes'])if node.get('name')=='breastcollar');node=g['nodes'][nodeid]
  if case=='removed_mesh':node.pop('mesh')
  elif case=='renamed_part':g['meshes'][node['mesh']]['name']='unexpected_breastcollar';node['name']='unexpected_breastcollar'
  elif case=='orphaned_part':
   for parent in g['nodes']:
    if 'children'in parent:parent['children']=[i for i in parent['children']if i!=nodeid]
   for scene in g['scenes']:scene['nodes']=[i for i in scene['nodes']if i!=nodeid]
   assert 'mesh'in node # Retained real geometry; only removed active-scene reachability.
  candidate=gzip.decompress(archive.read_bytes())if case=='original_as_candidate'else packed(g)
  target=root/'renderers/web/transport/harness/light_breastcollar_harness_reconstructed_01.glb';target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(candidate);receipt=O/(case+'-receipt.json');run=subprocess.run([sys.executable,str(root/'tools/transport/test_harness_body_fit.py'),str(receipt)],capture_output=True,text=True);(O/(case+'-output.txt')).write_text(run.stdout+run.stderr);assert run.returncode!=0,case;assert receipt.exists(),case;r=json.loads(receipt.read_text());assert r['baseline']['proper_crossings']==100;assert r['gear_sha256']==hashlib.sha256(candidate).hexdigest();after=r['repaired']
  if case=='original_as_candidate':assert after['proper_crossings']==100 and after['surface_pairs']>0 and len(after['clearance_violations'])>0
  else:assert after['active_part_triangles']['breastcollar']==0 and after['active_horse_triangles']==14172
  results.append({'case':case,'nonzero_exit':run.returncode,'diagnostic_receipt':str(receipt),'receipt_sha256':sha(receipt),'candidate_sha256':hashlib.sha256(candidate).hexdigest(),'active_part_triangles':after['active_part_triangles'],'active_horse_triangles':after['active_horse_triangles'],'surface_pairs':after['surface_pairs'],'proper_crossings':after['proper_crossings'],'clearance_violations':len(after['clearance_violations']),'last_error':run.stderr.strip().splitlines()[-1]})
summary={'installed_tool':str(tool),'installed_tool_sha256':sha(tool),'unchanged_input_horse_sha256':sha(horse),'unchanged_input_repaired_gear_sha256':sha(gear),'cases':results,'all_four_expected_failures_and_receipts_survive':True,'application_writes':False,'temporary_mirrors_cleaned':True};(O/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
