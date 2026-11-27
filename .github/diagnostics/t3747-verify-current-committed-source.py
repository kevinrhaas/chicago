import hashlib,json,os,subprocess,sys
from pathlib import Path
head=os.environ['DIAGNOSTIC_HEAD'];raw=subprocess.check_output(['git','show',head+':.github/diagnostics/t3747-current-committed-source.json'])
assert hashlib.sha256(raw).hexdigest()==os.environ['SOURCE_MANIFEST_SHA'];m=json.loads(raw)
assert m['role']=='committed-core' and subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==m['app_head']
assert subprocess.check_output(['git','write-tree'],text=True).strip()==m['candidate_tree']
assert not subprocess.check_output(['git','diff','--name-only','HEAD']).strip()
for p,h in m['source_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
for p,key in [('chicago/4d/tools/measure_still_frame.mjs','timing_helper_sha256'),('chicago/4d/tools/still_frame_ceilings.json','ceilings_sha256')]:assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==m[key]
r={**m,'workflowHead':head,'phase':'after' if '--verify' in sys.argv else 'before','allTrackedSourcePathsVerified':True,'actualCommittedAppHeadVerified':True}
Path(os.environ['SOURCE_RECEIPT_PATH']).write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k!='source_sha256'}))
