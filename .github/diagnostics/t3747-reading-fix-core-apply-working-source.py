"""CI: apply/verify the frozen complete uncommitted feature, without authoring it."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path

def git(*a):return subprocess.check_output(['git',*a])
def sha(b):return hashlib.sha256(b).hexdigest()
head=os.environ['DIAGNOSTIC_HEAD'];expected=os.environ['SOURCE_MANIFEST_SHA']
assert re.fullmatch('[0-9a-f]{40}',head)
manifest_path='.github/diagnostics/t3747-reading-fix-core-source.json'
patch_path='.github/diagnostics/t3747-reading-fix-core-source.patch'
cache=Path('/tmp/t3747-reading-fix-core-manifest.json')
if '--verify' not in sys.argv:
    raw=git('show',head+':'+manifest_path);assert sha(raw)==expected
    cache.write_bytes(raw);m=json.loads(raw)
    assert m['role']=='complete-uncommitted-feature' and m['qualifies_feature_candidate']
    assert git('rev-parse','HEAD').decode().strip()==m['base_dev']
    assert not git('diff','--name-only','HEAD').strip()
    sparse=subprocess.run(['git','config','--bool','core.sparseCheckout'],capture_output=True,text=True)
    if sparse.stdout.strip()=='true':subprocess.run(['git','sparse-checkout','add','chicago/4d/docs/measurements'],check=True)
    patch=git('show',head+':'+patch_path);assert sha(patch)==m['patch_sha256']
    p=Path('/tmp/t3747-reading-fix-core.patch');p.write_bytes(patch)
    subprocess.run(['git','apply','--index','--check',str(p)],check=True)
    subprocess.run(['git','apply','--index',str(p)],check=True)
raw=cache.read_bytes();assert sha(raw)==expected;m=json.loads(raw)
assert git('rev-parse','HEAD').decode().strip()==m['base_dev']
assert git('write-tree').decode().strip()==m['candidate_tree']
assert git('rev-parse',m['candidate_tree']+':chicago/4d').decode().strip()==m['candidate_app_tree']
assert set(git('diff','--cached','--name-only','HEAD').decode().splitlines())==set(m['source_sha256'])
assert not git('diff','--name-only').strip()
for p,h in m['source_sha256'].items():assert p.startswith('chicago/4d/') and sha(Path(p).read_bytes())==h,p
for p,k in [('chicago/4d/tools/measure_still_frame.mjs','timing_helper_sha256'),('chicago/4d/tools/still_frame_ceilings.json','ceilings_sha256')]:assert sha(Path(p).read_bytes())==m[k],p
plan=m['native_matrix']
assert len(plan)==9
for residue in range(32):
    assert sum(residue%int(row['part'].split('/')[1])==int(row['part'].split('/')[0])-1 for row in plan)==1
ordinal=0;drape=[]
for line in Path('chicago/4d/tools/check.sh').read_text().splitlines():
    if re.match(r'^\s*(?:every_part\s+)?(step|selftest) ',line):ordinal+=1
    if 'node tools/test_human_drape.mjs' in line:drape.append(ordinal)
assert drape==[m['drape_ordinal']]
serial=[row for row in plan if row['serial']];assert len(serial)==1
k,n=map(int,serial[0]['part'].split('/'));assert (drape[0]-1)%n==k-1
part=os.environ.get('NATIVE_PART')
if part:
    current=[row for row in plan if row['part']==part];assert len(current)==1
    if '--verify' in sys.argv and current[0]['serial']:assert os.environ['CHECK_JOBS']=='1'
reading={**m,'workflowHead':head,'candidateSourceIsWorkingTreePatch':True,'allTrackedSourcePathsVerified':True,'all32PartitionPlanAndClothingOrdinalVerified':True,'sourcePathCount':len(m['source_sha256']),'noAuthoredAppCommit':True,'measurementRasterGeometryPopulationLimitsUnchanged':True,'nativePart':os.environ.get('NATIVE_PART'),'nativeJobs':os.environ.get('CHECK_JOBS'),'phase':'after' if '--verify' in sys.argv else 'before'}
out=Path(os.environ.get('SOURCE_RECEIPT_PATH','chicago/4d/calibrated-source.json'));out.write_text(json.dumps(reading,indent=2)+'\n')
print(json.dumps({k:v for k,v in reading.items() if k!='source_sha256'}))
