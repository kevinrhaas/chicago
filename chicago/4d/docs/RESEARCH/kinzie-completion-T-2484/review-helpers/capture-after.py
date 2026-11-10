"""External actual canonical capture driver; execute only with Root GPU grant after native adoption.
Official photo_match writes the canonical pair/unreviewed record. This preserves every raw PNG
and generated unreviewed record before any direct reviewer adjudicates it. No verdict assigned.
"""
import argparse,hashlib,json,pathlib,re,shutil,subprocess,time
p=argparse.ArgumentParser()
for key in ['app','out','source-sha','retained-sha','native-run','adopted-head','house-sha','green-sha']:p.add_argument('--'+key,required=True)
a=p.parse_args();root=pathlib.Path(a.app).resolve();out=pathlib.Path(a.out).resolve();assert not out.exists(),'use a unique empty output directory'
for value in [a.source_sha,a.retained_sha,a.adopted_head]:assert re.fullmatch('[a-f0-9]{40}',value)
for value in [a.house_sha,a.green_sha]:assert re.fullmatch('[a-f0-9]{64}',value)
assert a.native_run.isdecimal()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==a.adopted_head
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
keys={'kinzie_house_1812':('kinzie_house_1812__kinzie_1804.glb',a.house_sha),'kinzie_house_1812_green':('kinzie_house_1812_green__kinzie_1804.glb',a.green_sha)}
for key,digest in keys.values():assert sha(root/'assets/gltf'/key)==digest
out.mkdir(parents=True);(out/'raw').mkdir();(out/'generated-unreviewed').mkdir();(out/'pre-capture-records').mkdir();(out/'logs').mkdir()
views=['chicago_magazine_1857','cram_1893','eastman_1820','gemmell_1820','lossing_1869','sarony_1912','teich_postcard'];rows=[]
for view in views:
 cam=pathlib.Path('data/reference_views/kinzie_house_1812')/(view+'.json');match=cam.with_suffix('.match.json');doc=json.load(open(root/cam));assert doc['scene']=='1812'and doc['also_render']==['kinzie_house_1812_green'];shutil.copyfile(root/match,out/'pre-capture-records'/match.name)
 started=time.time();result=subprocess.run(['node','tools/photo_match.mjs',str(cam)],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/'logs'/(view+'.log')).write_text(result.stdout);print(view,'exit',result.returncode,'seconds',round(time.time()-started,3),flush=True);assert result.returncode==0,result.stdout[-5000:]
 record=json.load(open(root/match));assert record['verdict']=='unreviewed','fresh actual inputs must not silently retain an old verdict';assert record['glb_sha256']==a.house_sha;assert record['camera_sha256']==sha(root/cam);assert record['photo_sha256']==sha((root/cam.parent/doc['photo']).resolve());assert {m['structure_id']:m['glb_sha256']for m in record['rendered_members']}=={k:v[1]for k,v in keys.items()}
 raw=re.search(r'^\s+(/tmp/[^\n]+-render\.png)$',result.stdout,re.M);assert raw;raw_dst=out/'raw'/(view+'-render.png');shutil.copyfile(raw.group(1),raw_dst);shutil.copyfile(root/match,out/'generated-unreviewed'/match.name)
 rows.append({'view':view,'native_run':a.native_run,'native_source':a.source_sha,'retained_native':a.retained_sha,'adopted_head':a.adopted_head,'MASTER_sha256':a.house_sha,'green_MASTER_sha256':a.green_sha,'camera_sha256':record['camera_sha256'],'photo_sha256':record['photo_sha256'],'group_sha256':record['group_sha256'],'members':record['rendered_members'],'pair':record['side_by_side'],'pair_sha256':sha(root/record['side_by_side']),'raw_png':str(raw_dst),'raw_sha256':sha(raw_dst),'exit_code':0,'seconds':round(time.time()-started,3),'verdict':'unreviewed'})
 (out/'RENDER-BINDINGS.json').write_text(json.dumps(rows,indent=2)+'\n')
for key,digest in keys.values():assert sha(root/'assets/gltf'/key)==digest
print('SEVEN ACTUAL AFTER PAIRS COMPLETE. No verdict assigned; direct source/pair review required.',flush=True)
