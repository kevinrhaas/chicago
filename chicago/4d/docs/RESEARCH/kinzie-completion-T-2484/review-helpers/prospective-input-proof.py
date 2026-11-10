"""Read-only prospective metadata/flora repair proof; no source mutation or native acceptance."""
import copy,hashlib,json,pathlib,sys,subprocess
repo=pathlib.Path('/tmp/nov10-kinzie-completion');app=repo/'chicago/4d';pin='6b11594bbd1d1a4e9fdd864878359ccf1c54edfc'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()==pin
sys.path[:0]=[str(app/'generators'),'/tmp/nov10-kinzie-native-qualification']
import mesh_inputs
from asset_overlay import FrozenAssetOverlay
binding=json.load(open('/tmp/nov10-kinzie-native-qualification/BEFORE-BINDING.json'))
assert binding['pinned_HEAD']==pin
rows=[];overlay=FrozenAssetOverlay(repo,pathlib.Path('/tmp/chicago-west-wicket-20261109/chicago/4d/assets'),pin).install()
try:
 for item in binding['affected']:
  st=json.load(open(repo/item['source_path']));phase=next(p for p in st['phases']if p['id']==item['phase_id']);old=mesh_inputs.structure_inputs_sha(st,phase,item['archetype']);assert old==item['current_inputs_sha256'],item['asset_key']
  proposed=copy.deepcopy(st)
  if st['id']=='kinzie_house_1812':
   ph=next(p for p in proposed['phases']if p['id']==item['phase_id']);ph['form']['end_openings']['note']+=' T-2484: end-door width follows the front prototype; its clear height is independently overridden by the stated reconstructed end_door_height_m=2.50m.'
  newphase=next(p for p in proposed['phases']if p['id']==item['phase_id']);new=mesh_inputs.structure_inputs_sha(proposed,newphase,item['archetype']);assert old==new,item['asset_key'];rows.append({'asset_key':item['asset_key'],'before_inputs_sha256':old,'prospective_after_inputs_sha256':new,'same':True})
finally:overlay.uninstall()
assert len(rows)==83
r={'status':'PASS_READ_ONLY_PROSPECTIVE_METADATA_FLORA_REPAIR_NATIVE_INPUT_INVARIANCE_NOT_APPLIED','source':pin,'records':83,'native_input_changes':0,'actual_SOURCE_asset_reads_authenticated':len(overlay.reads),'rows':rows,'claim_limit':'Candidate changes only a note on the house and the standalone flora planting file/notes, which is outside these83native input documents. Actual source edit still requires same proof afterward; no native output, smoke, runtime or picture acceptance.'}
pathlib.Path('/tmp/nov10-kinzie-ui/PROSPECTIVE-NATIVE-INPUTS-UNCHANGED.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k!='rows'},indent=2))
