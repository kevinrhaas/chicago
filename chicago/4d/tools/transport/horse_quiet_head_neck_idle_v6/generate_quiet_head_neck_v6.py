#!/usr/bin/env python3
"""New bounded quiet15 feature; all broader failed17 artifacts remain intact."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import argparse,copy,hashlib,json,resource,struct,time
from pathlib import Path
import numpy as np

PARENT='0ced8a09e27da047ad404c902e9d032e43654393027199db8dfd9c315be17929'
PAIR='a3eca1a164e2adf13d7d5f6699ff43de66d48dde0e3220f4aae90591dcaf4cb3'
HEAD='a9d9573368f48b4df839c3f246035aa7ac96b04ca098c37e015113266954cf8e'
NAME='sevket_reconstructed_quiet_head_neck_idle_v1'
NOTICE='chicago4d_quiet_head_neck_idle_v6'

def need(ok,message):
    if not ok:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(raw):
    magic,version,size,n,tag=struct.unpack_from('<5I',raw);need((magic,version,size,tag)==(0x46546c67,2,len(raw),0x4e4f534a),'complete GLB2')
    count,tag=struct.unpack_from('<2I',raw,20+n);need(tag==0x004e4942 and 28+n+count==len(raw),'complete BIN')
    return json.loads(raw[20:20+n]),raw[28+n:]
def write(doc,binary):
    text=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();text+=b' '*(-len(text)%4)
    return struct.pack('<5I',0x46546c67,2,28+len(text)+len(binary),len(text),0x4e4f534a)+text+struct.pack('<2I',len(binary),0x004e4942)+binary
def view(doc,binary,mesh,name):
    p=doc['meshes'][mesh]['primitives'][0];a=doc['accessors'][p['indices']if name=='indices'else p['attributes'][name]];v=doc['bufferViews'][a['bufferView']]
    width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dtype=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);need(not a.get('sparse')and not a.get('normalized'),'dense exact source stream')
    start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',width*dtype.itemsize)
    return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=start,strides=(stride,dtype.itemsize)),start,stride,width*dtype.itemsize
def dense(j,w):
    result=np.zeros((len(j),26))
    for row in range(len(j)):
        for k in range(4):
            if w[row,k]:
                need(0<=j[row,k]<26,'positive influence inside actual26joint palette');result[row,int(j[row,k])]+=float(w[row,k])
    return result
def quiet(source):
    old,natural=source['animations'];need(len(old['channels'])==13 and len(natural['channels'])==17,'original13/17 inventory')
    need(old['channels']==natural['channels'][:13]and old['samplers']==natural['samplers'][:13],'all13 original curves exact prefix')
    need([(c['target']['node'],c['target']['path'])for c in natural['channels'][13:]]==[(2,'rotation'),(3,'rotation'),(4,'rotation'),(5,'rotation')],'exact four added source gestures')
    return dict(name=NAME,samplers=copy.deepcopy(natural['samplers'][:15]),channels=copy.deepcopy(natural['channels'][:15]),
                extras=dict(feature_scope='reconstructed quiet head and neck idle; inherited planted body/legs; tail gesture not included',
                            omitted_source17_channels=[15,16],source17_unqualified=True,qualification='UNRUN',walk_trot_riding=False))
def notice(parent,recipe,role):
    return dict(source_parent_sha256=parent,head_template_sha256=HEAD,recipe_sha256=recipe,binding_version=6,
                role=role,selected_clip=NAME if role=='quiet15-candidate'else None,qualification='UNRUN',old_certificate_transferred=False)
def export(parent,head,recipe,parent_sha,role):
    doc,binary=read(parent);hd,hb=read(head);p=view(doc,binary,0,'POSITION')[0];hp=view(hd,hb,0,'POSITION')[0]
    need(np.array_equal(p,hp),'source and head template geometry identical');mask=(p[:,1]>1.04)&(p[:,2]>.28);need(int(mask.sum())==2306,'entire declared head component')
    out=bytearray(binary)
    for name in ('JOINTS_0','WEIGHTS_0'):
        rows,start,stride,width=view(doc,binary,0,name);template=view(hd,hb,0,name)[0]
        for row in np.flatnonzero(mask):
            offset=start+int(row)*stride;out[offset:offset+width]=template[row].tobytes()
    child=copy.deepcopy(doc)
    if role=='quiet15-candidate':child['animations'].append(quiet(doc))
    child.setdefault('asset',{}).setdefault('extras',{})[NOTICE]=notice(parent_sha,recipe,role)
    result=write(child,out);need(len(result)<=4*1024**2,'unchanged fourMiB master cap')
    return result
def admission(parent,child,head,recipe,parent_sha,role):
    pd,pb=read(parent);cd,cb=read(child);hd,hb=read(head);clean=copy.deepcopy(cd)
    need(clean['asset']['extras'].pop(NOTICE,None)==notice(parent_sha,recipe,role),'exact new quiet feature parent/head/recipe/selected-name notice')
    if role=='quiet15-candidate':
        actual=clean['animations'].pop();expected=quiet(pd)
        # Independently characterize the omission, not just a count or name.
        natural=pd['animations'][1];retained=[c for c in natural['channels']if c['target']['node']not in(4,5)]
        need(actual['name']==NAME and len(actual['channels'])==15 and actual['channels']==retained,'quiet selects all and only original13 plus exactNECK2/HEAD3; added tail gesture omitted')
        need(actual==expected,'all retained quiet sampler/time/curve/interpolation references exact source17')
    need(clean==pd and len(pb)==len(cb),'original13/failed17/rig/geometry/image metadata retained exactly')
    pos=view(pd,pb,0,'POSITION')[0];mask=(pos[:,1]>1.04)&(pos[:,2]>.28);s=((pos[:,1].astype(float)-1.3)*.18+(pos[:,2].astype(float)-.55)*.48)/(.18**2+.48**2);core=mask&(s>=.9)
    allowed=bytearray(len(pb));changed_rows=set()
    for name in ('JOINTS_0','WEIGHTS_0'):
        old,start,stride,width=view(pd,pb,0,name);actual=view(cd,cb,0,name)[0]
        for row in np.flatnonzero(mask):allowed[start+int(row)*stride:start+int(row)*stride+width]=b'\1'*width
        changed_rows.update(np.flatnonzero((old!=actual).any(axis=1)).tolist())
    changed=np.flatnonzero(np.frombuffer(pb,dtype='u1')!=np.frombuffer(cb,dtype='u1'))
    need(all(allowed[int(i)]for i in changed),'TAIL969/BODY/EYE/geometry/images/clips/all non-head BIN bytes exactV2')
    j=view(cd,cb,0,'JOINTS_0')[0];w=view(cd,cb,0,'WEIGHTS_0')[0];oj=view(pd,pb,0,'JOINTS_0')[0];ow=view(pd,pb,0,'WEIGHTS_0')[0]
    need(np.isfinite(w).all()and(w>=0).all(),'finite nonnegative weights')
    mass=float(np.abs(w.astype(float).sum(axis=1)-ow.astype(float).sum(axis=1)).max());need(mass<2e-7,'source mass retained')
    sem=dense(j,w);osem=dense(oj,ow);classes={}
    for row,point in enumerate(pos):classes.setdefault(tuple(np.rint(point.astype(float)/1e-6).astype('i8')),[]).append(row)
    for rows in classes.values():need(all(np.array_equal(sem[rows[0]],sem[row])for row in rows),'canonical weld class equality')
    need(np.array_equal(j[core],oj[core])and np.array_equal(w[core],ow[core]),'all1184 original rigid skull core tuples exact')
    free=mask&(s>.48)&(s<.9)
    for row in np.flatnonzero(free):
        a=sem[row].copy();b=osem[row].copy();a[[2,3]]=0;b[[2,3]]=0;need(np.array_equal(a,b),'original palette/residual influences exact')
    for name in ('JOINTS_0','WEIGHTS_0'):
        need(np.array_equal(view(cd,cb,0,name)[0][mask],view(hd,hb,0,name)[0][mask]),'all2306 V4 head tuples byte-exact')
        need(np.array_equal(view(cd,cb,0,name)[0][~mask],view(pd,pb,0,name)[0][~mask]),'all969 original V2 tail tuples exact')
    return dict(changed_HEAD_rows=len(changed_rows),changed_BIN_bytes=len(changed),maximum_mass_delta=mass,head_rows=2306,tail_rows=969,
                all1184_core_exact=True,all_original13_and_failed17_bytes_retained=True,HEAD_exactV4=True,TAIL_exactV2=True,
                source_weld_classes=len(classes))
def pair_admission(parent,reference,candidate,paired,head,recipe):
    reports=[admission(parent,candidate,head,recipe,PARENT,'quiet15-candidate'),admission(reference,paired,head,recipe,PAIR,'paired925-head-neck-reference')]
    cd,cb=read(candidate);pd,pb=read(paired)
    for mesh in range(3):
        for name in ('JOINTS_0','WEIGHTS_0'):need(np.array_equal(view(cd,cb,mesh,name)[0],view(pd,pb,mesh,name)[0]),'entire actual candidate/paired925 skin streams equal')
    return reports
def controls(parent,reference,candidate,paired,head,recipe):
    doc,binary=read(candidate);pd,pb=read(parent);pos=view(doc,binary,0,'POSITION')[0];mask=(pos[:,1]>1.04)&(pos[:,2]>.28);s=((pos[:,1].astype(float)-1.3)*.18+(pos[:,2].astype(float)-.55)*.48)/(.18**2+.48**2);free=mask&(s>.48)&(s<.9);core=mask&(s>=.9)
    j=view(doc,binary,0,'JOINTS_0')[0];w=view(doc,binary,0,'WEIGHTS_0')[0];classes={}
    for row,p in enumerate(pos):classes.setdefault(tuple(np.rint(p.astype(float)/1e-6).astype('i8')),[]).append(row)
    single=next(rows[0]for rows in classes.values()if len(rows)==1 and free[rows[0]]and min(w[rows[0],:2])>0)
    weld=next(rows for rows in classes.values()if len(rows)>1 and free[rows[0]]and min(w[rows[0],:2])>0)
    skull=next(rows[0]for rows in classes.values()if len(rows)==1 and core[rows[0]])
    def byte(mesh,name,row=0):
        out=bytearray(binary);_,start,stride,_=view(doc,binary,mesh,name);out[start+row*stride]^=1;return write(doc,out)
    def tuple_change(row,mode):
        out=bytearray(binary)
        if mode=='palette':
            a,start,stride,_=view(doc,binary,0,'JOINTS_0');out[start+row*stride:start+row*stride+a.dtype.itemsize]=np.array(6,dtype=a.dtype).tobytes()
        else:
            a,start,stride,_=view(doc,binary,0,'WEIGHTS_0');delta=.25*float(min(a[row,:2]))if mode=='weld'else .1
            pairs=[(0,float(a[row,0])+delta)]if mode=='mass'else[(0,float(a[row,0])+delta),(1,float(a[row,1])-delta)]
            for k,value in pairs:offset=start+row*stride+k*a.dtype.itemsize;out[offset:offset+a.dtype.itemsize]=np.array(value,dtype=a.dtype).tobytes()
        return write(doc,out)
    def metadata(change):
        altered=copy.deepcopy(doc);change(altered);return write(altered,binary)
    cases=[]
    cases.append(('wrong omission keeps tail and drops head',metadata(lambda d:d['animations'][2]['channels'].__setitem__(14,copy.deepcopy(d['animations'][1]['channels'][15]))),paired))
    cases.append(('missing selected quiet name',metadata(lambda d:d['animations'][2].__setitem__('name','wrong_clip')),paired))
    cases.append(('silently select failed17',metadata(lambda d:d['asset']['extras'][NOTICE].__setitem__('selected_clip',d['animations'][1]['name'])),paired))
    cases.append(('retained curve interpolation changed',metadata(lambda d:d['animations'][2]['samplers'][13].__setitem__('interpolation','STEP')),paired))
    cases.append(('original13 clip changed',metadata(lambda d:d['animations'][0].__setitem__('name','changed_old13')),paired))
    cases.append(('failed17 artifact rewritten',metadata(lambda d:d['animations'][1].__setitem__('name','changed_failed17')),paired))
    # Change actual retained neck quaternion bytes, not merely its metadata.
    acc=doc['accessors'][232];bv=doc['bufferViews'][acc['bufferView']];altered=bytearray(binary);altered[bv.get('byteOffset',0)+acc.get('byteOffset',0)]^=1
    cases.append(('retained head-neck curve bytes altered',write(doc,altered),paired))
    cases.extend([('original tail field changed',byte(0,'WEIGHTS_0',int(np.flatnonzero(~mask)[0])),paired),('BODY geometry changed',byte(1,'POSITION'),paired),('EYE geometry changed',byte(2,'POSITION'),paired),('HAIR geometry changed',byte(0,'POSITION'),paired)])
    altered=bytearray(binary);a,start,stride,_=view(doc,binary,0,'WEIGHTS_0');altered[start+skull*stride:start+skull*stride+4]=np.array(.99,dtype=a.dtype).tobytes();ja,js,jt,_=view(doc,binary,0,'JOINTS_0');altered[js+skull*jt+ja.dtype.itemsize:js+skull*jt+2*ja.dtype.itemsize]=np.array(2,dtype=ja.dtype).tobytes();altered[start+skull*stride+4:start+skull*stride+8]=np.array(.01,dtype=a.dtype).tobytes()
    cases.extend([('rigid skull core changed',write(doc,altered),paired),('single welded member changed with mass preserved',tuple_change(weld[0],'weld'),paired),('forbidden palette joint',tuple_change(single,'palette'),paired),('weight mass changed',tuple_change(single,'mass'),paired)])
    image=doc['bufferViews'][doc['images'][0]['bufferView']];altered=bytearray(binary);altered[image.get('byteOffset',0)]^=1;cases.append(('original image bytes changed',write(doc,altered),paired));cases.append(('wrong paired ancestry',candidate,candidate))
    # All free rows of a whole weld class are restored to V2: mass, palette and
    # weld equality survive, but the approved exact V4 HEAD field must refuse it.
    altered=bytearray(binary)
    for semantic in ('JOINTS_0','WEIGHTS_0'):
        old=view(pd,pb,0,semantic)[0];_,start,stride,width=view(doc,binary,0,semantic)
        for row in weld:altered[start+row*stride:start+row*stride+width]=old[row].tobytes()
    cases.append(('approved V4 head field replaced by V2 class',write(doc,altered),paired))
    results=[]
    for label,bad,bad_pair in cases:
        need(bad!=candidate or bad_pair!=paired,'meaningful nonidentity mutation')
        try:pair_admission(parent,reference,bad,bad_pair,head,recipe)
        except(ValueError,KeyError,IndexError)as e:results.append(dict(control=label,detected=True,reason=str(e),mutant_sha256=sha(bad)))
        else:raise ValueError('Mutation escaped:'+label)
    return results
def main():
    resource.setrlimit(resource.RLIMIT_CPU,(10,11));parser=argparse.ArgumentParser(description=__doc__)
    for name in ('parent','reference','head_template','recipe','candidate_out','paired_out','report_out'):parser.add_argument('--'+name.replace('_','-'),required=True,type=Path)
    args=parser.parse_args();need(all(not p.exists()for p in(args.candidate_out,args.paired_out,args.report_out)),'fresh outside outputs')
    start=time.process_time();parent=args.parent.read_bytes();reference=args.reference.read_bytes();head=args.head_template.read_bytes();recipe=args.recipe.read_bytes();spec=json.loads(recipe)
    need(sha(parent)==PARENT and sha(reference)==PAIR and sha(head)==HEAD,'immutable V2/V4 source identities')
    need(spec['schema']=='quiet_head_neck_idle_v6'and spec['selected_clip']==NAME and spec['retained_channels']==list(range(15))and spec['omitted_added_tail_channels']==[15,16],'explicit narrower quiet15 feature, no curve retune')
    candidate=export(parent,head,sha(recipe),PARENT,'quiet15-candidate');paired=export(reference,head,sha(recipe),PAIR,'paired925-head-neck-reference')
    checks=pair_admission(parent,reference,candidate,paired,head,sha(recipe));negative=controls(parent,reference,candidate,paired,head,sha(recipe))
    report=dict(status='QUIET15_SOURCE_EXPORT_AND_MUTATION_CONTROLS_ONLY_PASS_NATIVE_UNRUN',candidate_sha256=sha(candidate),paired925_sha256=sha(paired),candidate_bytes=len(candidate),paired925_bytes=len(paired),producer_sha256=sha(Path(__file__).read_bytes()),recipe_sha256=sha(recipe),selected_clip=NAME,selected_track_count=15,retained_unqualified17=True,source_admission=checks,negative_controls=negative,CPU_seconds=time.process_time()-start,canonical_install=False,native_old13='UNRUN',native_quiet15='UNRUN',paired925='UNRUN',native_world='UNRUN',runtime_adoption=False,tail_gesture_walk_trot_riding=False)
    args.candidate_out.write_bytes(candidate);args.paired_out.write_bytes(paired);args.report_out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
