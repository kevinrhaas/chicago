"""Apply only the proven post-retention flora/prose repair in the assigned Kinzie worktree.
Requires exact qualified adopted HEAD, and proves all83 native input hashes remain frozen.
No geometry/native assets/camera values/grades/species/counts/heights are modified.
"""
import argparse,copy,json,pathlib,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--adopted-head',required=True);a=p.parse_args()
repo=pathlib.Path('/tmp/nov10-kinzie-completion');root=repo/'chicago/4d';assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()==a.adopted_head
assert not subprocess.check_output(['git','status','--porcelain=v1'],cwd=repo,text=True).strip()
bind=json.load(open('/tmp/nov10-kinzie-native-qualification/BEFORE-BINDING.json'));assert bind['pinned_HEAD']=='6b11594bbd1d1a4e9fdd864878359ccf1c54edfc'
sys.path.insert(0,str(root/'generators'));import mesh_inputs
before={};records={}
for x in bind['affected']:
 st=json.load(open(repo/x['source_path']));phase=next(p for p in st['phases']if p['id']==x['phase_id']);h=mesh_inputs.structure_inputs_sha(st,phase,x['archetype']);assert h==x['current_inputs_sha256'],x['asset_key'];before[x['asset_key']]=h;records[x['structure_id']]=st
housepath=root/'data/structures/kinzie_house_1812.json';house=records['kinzie_house_1812'];note=house['phases'][0]['form']['end_openings']['note'];old="the door and window take the front's sizes and the lights the archetype's 0.7 by 0.8 m: none of the pictures measures them."
assert old in note
house['phases'][0]['form']['end_openings']['note']=note.replace(old,"the window and door width take the front's prototypes and the lights the archetype's0.7by0.8m. T-2484 explicitly overrides the west door's clear height to2.50m via reconstructed end_door_height_m; its0.02m sill gives a2.52m head under the3.0m wall plate. None is a historical measured dimension.")
housepath.write_text(json.dumps(house,indent=2,ensure_ascii=False)+'\n')
treepath=root/'data/flora/plantings/kinzie_house_1812_trees.json';trees=json.load(open(treepath));row=[331.2,327.2,323.2,319.2];i=0
for stem in trees['stems']:
 if stem['species']!='populus_nigra_italica':continue
 stem['at_local_enu_m']=[1156.0,row[i]];i+=1
 stem['note']=stem['note'].replace('at4.5m stations from N332.7 to319.2','at4.0m stations from N331.2 to319.2')+' The nearest stem is4.80m from the actual house footprint, clearing the existing4.5m planter exclusion; the earlier N332.7 trial would be refused at3.3m. This clearance adjustment changes no historical source claim.'
assert i==4
trees['research_note']="WHAT WOULD MOVE THESE. A measured plan of the Kinzie lot or a planting account locating the trees rather than naming them. Sarony's lithograph after Juliette Kinzie's household sketch is now in the public image store as chicago_kinzie_residence_sarony_currey_1912.png and source sarony_kinzie_residence_currey_1912_plate; it was directly read with all six other pictures for T-2484. The four north/south poplar stations, exact spacing and all six heights/positions remain reconstructed in L-kinzie-house-completion-2484, not surveyed from image pixels. The four stations are N331.2,327.2,323.2,319.2 at E1156,4.0m apart: the north stem clears the actual house footprint by4.80m against the renderer's existing4.5m margin. T-3106's in_structure names only the green's fenced plot; it never exempts the house, other buildings or travelled tracks. Both cottonwoods keep their existing coordinates, species and heights. The ByGrade colours describe their inferred species appearance; these exact planting positions and heights remain liberties."
treepath.write_text(json.dumps(trees,indent=2,ensure_ascii=False)+'\n')
libpath=root/'docs/LIBERTIES.md';raw=libpath.read_bytes();text=raw.decode();old='green, at E1156.0 and N332.7,328.2,323.7,319.2, is reconstructed, with its4.5m spacing.';new='green, at E1156.0 and N331.2,327.2,323.2,319.2, is reconstructed, with its4.0m spacing.\nThe actual planter excludes stems within4.5m of another building. The north stem now\nclears the house footprint by4.80m; the earlier N332.7 station would be refused at3.3m.\nThis finite clearance adjustment changes no historical source claim. The ByGrade\ncolours describe their inferred species appearance; the exact planting positions and\nheights listed here remain liberties.'
assert text.count(old)==1;libpath.write_bytes(text.replace(old,new).encode())
rows=[]
for x in bind['affected']:
 st=json.load(open(repo/x['source_path']));phase=next(p for p in st['phases']if p['id']==x['phase_id']);h=mesh_inputs.structure_inputs_sha(st,phase,x['archetype']);assert h==before[x['asset_key']],x['asset_key'];rows.append({'asset_key':x['asset_key'],'before_inputs_sha256':before[x['asset_key']],'after_inputs_sha256':h,'same':True})
proof={'status':'PASS_ACTUAL_POST_RETENTION_FLORA_PROSE_REPAIR_ALL83_NATIVE_INPUTS_UNCHANGED','adopted_head':a.adopted_head,'native_source':bind['pinned_HEAD'],'native_defaults':83,'changed_native_input_hashes':0,'tree_stations':row,'first_house_clearance_m':4.8,'existing_clearance_margin_m':4.5,'rows':rows,'limits':'Actual authored data and resolved native input proof. Not runtime planted-stem acceptance, picture acceptance, protected gate or historical measurement.'}
(root/'docs/RESEARCH/kinzie-completion-T-2484/POST-RETENTION-INPUTS-UNCHANGED.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items()if k!='rows'},indent=2))
