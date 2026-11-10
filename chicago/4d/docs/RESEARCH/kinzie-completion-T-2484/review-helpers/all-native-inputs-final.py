"""Recompute every registered default+variant native recipe on the adopted corrected source.
Sparse asset reads use actual own files or unchanged Root files, each Git-SHA1 authenticated;
never copy or modify Root assets. This is input freshness, not output/runtime acceptance.
"""
from pathlib import Path
import hashlib,json,stat,subprocess,sys,time
repo=Path('/tmp/nov10-kinzie-completion');app=repo/'chicago/4d';head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip();assert head=='80ff2d2a64425fc8f50325411f3dcc0a45939dc1';assert not subprocess.check_output(['git','status','--porcelain=v1'],cwd=repo,text=True).strip()
sys.path[:0]=[str(app/'generators'),'/tmp/nov10-kinzie-native-qualification'];import mesh_inputs,terrain_inputs
from asset_overlay import FrozenAssetOverlay
ov=FrozenAssetOverlay(repo,Path('/tmp/chicago-west-wicket-20261109/chicago/4d/assets'),head).install();original_read,original_stat=ov._read,ov._stat
reads={}
def selected(p):
 key=ov.key(p)
 if key is None:return p,None
 try:
  if stat.S_ISREG(original_stat(p).st_mode):return p,key
 except FileNotFoundError:pass
 return ov.actual/key,key
def rd(p):
 actual,key=selected(p);raw=original_read(actual)
 if key in ov.oids:
  got=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert got==ov.oids[key],('SOURCE Git asset mismatch',key,got,ov.oids[key]);reads[key]={'path':str(actual),'git_blob':got,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 return raw
def ps(p,*args,**kw):
 actual,key=selected(p);return original_stat(actual,*args,**kw)
Path.read_bytes=rd;Path.stat=ps
rows=[];failures=[];began=time.time()
try:
 manifest=json.loads((app/'assets/manifest.json').read_text());versions=json.loads((app/'assets/manifest.versions.json').read_text())
 for kind,entries in [('default',manifest['assets']),('variant',versions['assets'])]:
  for key,e in sorted(entries.items()):
   try:
    if e.get('structure_id'):
     source=app/'data/structures'/((e['structure_id']+'.json')if kind=='default'else('versions/'+e['structure_id']+'/'+e['version_label']+'.json'))
     st=json.loads(source.read_text());phase=next(p for p in st['phases']if p['id']==e['phase_id']);got=mesh_inputs.structure_inputs_sha(st,phase,e.get('archetype'))
    else:
     assert e.get('terrain_epoch');got=terrain_inputs.terrain_inputs_sha(app/'data/terrain/epochs'/e['terrain_epoch'])
    assert got==e['inputs_sha256'],(key,got,e['inputs_sha256']);rows.append({'kind':kind,'asset_key':key,'inputs_sha256':got,'fresh':True})
   except Exception as error:failures.append({'kind':kind,'asset_key':key,'error':str(error)})
finally:ov.uninstall()
result={'status':'PASS_ALL1050_REGISTERED_NATIVE_INPUTS_FRESH'if not failures and len(rows)==1050 else'FAIL_ALL_NATIVE_INPUT_READ_OR_FRESHNESS','source_head':head,'seconds':round(time.time()-began,3),'fresh':len(rows),'defaults':sum(r['kind']=='default'for r in rows),'variants':sum(r['kind']=='variant'for r in rows),'rows':rows,'failures':failures,'actual_sparse_asset_reads_git_authenticated':reads,'claim_limit':'Actual native input recipes for all registered outputs recomputed. Sparse asset aliases are exact SOURCE Git blobs. Does not replace protected full source checks, native binary/control/foreign audit, image acceptance or published runtime review.'}
out=Path('/tmp/nov10-kinzie-ui/ALL1050-NATIVE-INPUTS-FRESH-POST-OWNERS.json');out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['rows','actual_sparse_asset_reads_git_authenticated']},indent=2));assert not failures and len(rows)==1050
