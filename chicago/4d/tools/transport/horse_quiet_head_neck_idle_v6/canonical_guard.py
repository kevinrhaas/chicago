"""Current indexed first-class source guard; old81 history is never retargeted."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parent
APP=ROOT.parents[2]
REPO=APP.parents[1]
E={**os.environ,'GIT_NO_LAZY_FETCH':'1'}
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(ok,why):
    if not ok:raise ValueError(why)
def git(*a):return subprocess.check_output(['git',*a],cwd=REPO,env=E)
def code_pins():
    declared=json.loads((ROOT/'CODE-PIN-PATHS.json').read_bytes())
    actual={name:sha((APP/p).read_bytes()) for name,p in declared['paths'].items()}
    for k,v in declared['preserved_old47_expected_sha256'].items():need(actual[k]==v,'immutable old47 code '+k)
    for k,v in declared['preserved_old36_expected_sha256'].items():need(actual[k]==v,'immutable old36 code '+k)
    return actual

def snapshot():
    need(not git('diff','--name-only').strip(),'All current source must be staged before qualification')
    semantic=git('ls-files','--stage','-z');entries={}
    for item in semantic.decode().split('\0'):
        if not item:continue
        metadata,name=item.split('\t');mode,blob,stage=metadata.split(' ');need(stage=='0','No unresolved index stages');entries[name]=(mode,blob)
    old=json.loads((ROOT/'PRESERVED-OLD81-SOURCE.json').read_bytes())
    exceptions={'chicago/4d/assets/LICENSES.md','chicago/4d/renderers/web/transport/LICENSES.md'}
    for r in old['source_files']:
        b=(REPO/r['path']).read_bytes()
        if r['path'] in exceptions:need(len(b)>=r['bytes'] and sha(b[:r['bytes']])==r['sha256'],'Exact original licence prefix '+r['path'])
        else:need(len(b)==r['bytes'] and sha(b)==r['sha256'],'Protected original81 source '+r['path'])
    audit=json.loads((ROOT/'INPUTS.json').read_bytes());declared=json.loads((ROOT/'CODE-PIN-PATHS.json').read_bytes())
    for name,r in audit['inputs'].items():
        b=(APP/r['path']).read_bytes();need(len(b)==r['bytes'] and sha(b)==r['sha256'],'Actual first-class input '+name)
    paths={r['path'] for r in old['source_files']}
    paths.update(str((APP/r['path']).relative_to(REPO)) for r in audit['inputs'].values())
    paths.update(str((APP/p).relative_to(REPO)) for p in declared['paths'].values())
    paths.update(x for x in git('diff','--cached','--name-only','-z','HEAD').decode().split('\0') if x)
    files=[]
    for relative in sorted(paths):
        p=REPO/relative;need(p.is_file() and not p.is_symlink(),'Ordinary current source '+relative)
        b=p.read_bytes();need(relative in entries,'All first-class inputs indexed '+relative)
        mode,blob=entries[relative];actual=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();need(blob==actual,'Working source equals actual indexed blob '+relative)
        files.append(dict(path=relative,mode=mode,blob=blob,bytes=len(b),sha256=sha(b)))
    mirror=REPO/'site/4d';mirror_rows=[]
    if mirror.exists():
        for p in sorted(mirror.rglob('*')):
            need(not p.is_symlink(),'Ordinary published mirror')
            if p.is_file():
                b=p.read_bytes();mirror_rows.append(dict(path=str(p.relative_to(mirror)),bytes=len(b),sha256=sha(b)))
    tree=git('write-tree').decode().strip()
    return dict(base_HEAD=git('rev-parse','HEAD').decode().strip(),TREE=tree,APP=git('rev-parse',tree+':chicago/4d').decode().strip(),semantic_index_sha256=sha(semantic),semantic_index_entries=len(entries),source_files=files,code_pins=code_pins(),old81_preserved_except_two_reviewed_append_only_licences=True,mirror=dict(exists=mirror.exists(),files=mirror_rows))

if __name__=='__main__':print(json.dumps(snapshot(),separators=(',',':')))
