"""Publish this exact locally committed tree/commit through GitHub Git API, non-force.
Normal git send-pack in the partial clone repeatedly demands unrelated missing historical
blobs. API publication authenticates every blob/tree/commit SHA and only fast-forwards our ref.
"""
import base64,concurrent.futures,datetime,hashlib,json,pathlib,re,subprocess,sys,time
repo=pathlib.Path('/tmp/nov10-kinzie-completion');out=pathlib.Path('/tmp/nov10-kinzie-source');head=sys.argv[1];base=sys.argv[2];branch='steward/t2484-kinzie-house-completion-20261110';receipt={'status':'RUNNING_EXACT_GIT_API_NONFORCE_PUBLICATION','commit':head,'base':base,'branch':branch,'blobs':[]}
def local(*args):return subprocess.check_output(['git',*args],cwd=repo)
def api(method,endpoint,data=None):
 argv=['gh','api','--method',method,'repos/kevinrhaas/chicago/'+endpoint]
 if data is not None:argv+=['--input','-']
 p=subprocess.run(argv,input=json.dumps(data).encode()if data is not None else None,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if p.returncode:raise RuntimeError(endpoint+': '+p.stderr.decode()[:2000])
 return json.loads(p.stdout)
def save(): (out/('EXACT-API-PUBLICATION-'+head[:8]+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
assert re.fullmatch('[a-f0-9]{40}',head)and re.fullmatch('[a-f0-9]{40}',base)
actual=api('GET','git/ref/heads/'+branch)['object']['sha'];receipt['before_ref']=actual;save()
if actual==head:receipt['status']='ALREADY_PUBLIC_EXACT_COMMIT';save();print('Already public exact commit',head);sys.exit(0)
assert subprocess.run(['git','merge-base','--is-ancestor',actual,head],cwd=repo).returncode==0,'Remote branch is not an ancestor; refuse overwrite'
entries=[]
for line in local('diff-tree','--no-commit-id','--no-renames','--raw','-r',base,head).decode().splitlines():
 meta,name=line.split('\t',1);oldmode,mode,oldoid,oid,status=meta[1:].split();assert mode=='100644'and status in ['A','M'],(mode,status,name);entries.append({'path':name,'mode':mode,'type':'blob','sha':oid})
assert entries

def upload(entry):
 oid=entry['sha'];b=local('cat-file','blob',oid);assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid
 remote=api('POST','git/blobs',{'encoding':'base64','content':base64.b64encode(b).decode()});assert remote['sha']==oid
 return {'path':entry['path'],'sha':oid,'bytes':len(b)}
with concurrent.futures.ThreadPoolExecutor(max_workers=6)as pool:
 for item in pool.map(upload,entries):receipt['blobs'].append(item);save();print('Uploaded exact blob',len(receipt['blobs']),len(entries),item['path'],flush=True)
base_tree=local('rev-parse',base+'^{tree}').decode().strip();tree=api('POST','git/trees',{'base_tree':base_tree,'tree':entries});expected_tree=local('rev-parse',head+'^{tree}').decode().strip();assert tree['sha']==expected_tree,(tree['sha'],expected_tree);receipt['exact_tree']=tree['sha'];save()
raw=local('cat-file','commit',head);header,message=raw.split(b'\n\n',1);fields={};parents=[]
for line in header.decode().splitlines():
 key,value=line.split(' ',1)
 if key=='parent':parents.append(value)
 else:fields[key]=value
assert set(fields)=={'tree','author','committer'}and parents==[base]
def person(value):
 m=re.fullmatch(r'(.*) <([^>]+)> (\d+) ([+-]\d{4})',value);assert m;name,email,timestamp,tz=m.groups();sign=1 if tz[0]=='+'else-1;zone=datetime.timezone(sign*datetime.timedelta(hours=int(tz[1:3]),minutes=int(tz[3:])));return {'name':name,'email':email,'date':datetime.datetime.fromtimestamp(int(timestamp),zone).isoformat()}
body={'tree':expected_tree,'parents':parents,'author':person(fields['author']),'committer':person(fields['committer']),'message':message.decode()}
commit=api('POST','git/commits',body)
if commit['sha']!=head:
 body['message']=message.decode().rstrip('\n');commit=api('POST','git/commits',body)
assert commit['sha']==head,('API commit serialization differs; refuse update',commit['sha'],head);receipt['exact_commit']=commit['sha'];save()
updated=api('PATCH','git/refs/heads/'+branch,{'sha':head,'force':False});assert updated['object']['sha']==head
readback=api('GET','git/ref/heads/'+branch)['object']['sha'];assert readback==head;receipt['public_ref_readback']=readback;receipt['status']='PASS_EXACT_BLOBS_TREE_COMMIT_AND_NONFORCE_BRANCH_FAST_FORWARD';save();print('PUBLIC EXACT SOURCE CHECKPOINT',head,flush=True)
