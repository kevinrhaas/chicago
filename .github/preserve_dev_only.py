"""DEV-only publication guard. No application generation and no Git mutation."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, os, shutil, stat, subprocess, tarfile, tempfile, zipfile

def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def validate_baseline(policy, run, artifact, live_build):
    assert run['id'] == policy['run_id']
    assert run['head_sha'] == policy['production_sha']
    assert run['head_branch'] == 'main' and run['conclusion'] == 'success' and run['status'] == 'completed'
    assert artifact['id'] == policy['artifact_id'] and artifact['name'] == policy['artifact_name']
    assert artifact['expired'] is False and artifact['size_in_bytes'] == policy['artifact_zip_bytes']
    assert artifact['digest'] == policy['artifact_digest']
    assert len(live_build['version']) >= 7 and policy['production_sha'].startswith(live_build['version'])

def seed_site(archive, destination, policy, live_build_bytes):
    archive, destination = Path(archive), Path(destination)
    assert not destination.exists(), 'Seed destination must be absent'
    assert archive.stat().st_size == policy['artifact_zip_bytes']
    assert 'sha256:' + digest_file(archive) == policy['artifact_digest']
    temporary = Path(tempfile.mkdtemp(prefix='site-seed-', dir=destination.parent))
    try:
        directory_modes = {}; seen_members = set()
        with zipfile.ZipFile(archive) as z:
            assert z.namelist() == ['artifact.tar'], 'Unexpected Pages artifact archive members'
            assert z.getinfo('artifact.tar').file_size <= policy['site_limit_bytes'] + 32 * 1024 * 1024
            with z.open('artifact.tar') as stream, tarfile.open(fileobj=stream, mode='r|*') as tar:
                count = total = 0
                for entry in tar:
                    path = PurePosixPath(entry.name)
                    assert not path.is_absolute() and '..' not in path.parts and '\\' not in entry.name
                    assert entry.isdir() or entry.isfile(), 'Links and special files are forbidden'
                    assert path.parts not in seen_members, 'Duplicate Pages artifact member'
                    seen_members.add(path.parts)
                    assert entry.mode & ~0o777 == 0, 'Special permission bits are forbidden'
                    target = temporary.joinpath(*path.parts)
                    if entry.isdir():
                        target.mkdir(parents=True, exist_ok=True)
                        directory_modes[target] = entry.mode & 0o777
                        continue
                    assert not target.exists(), 'Duplicate Pages artifact member'
                    count += 1; total += entry.size
                    assert count <= 100000 and total <= policy['site_limit_bytes']
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(entry) as src, target.open('xb') as dst: shutil.copyfileobj(src, dst)
                    os.chmod(target, entry.mode & 0o777)
        assert temporary in directory_modes, 'Pages artifact has no explicit root-directory mode'
        for directory, mode in sorted(directory_modes.items(), key=lambda item:len(item[0].parts), reverse=True):
            os.chmod(directory, mode)
        assert (temporary / '4d/build.json').read_bytes() == live_build_bytes, 'Archive marker differs from actual live production body'
        assert (temporary / 'robots.txt').is_file()
        assert b'Disallow: /4d/dev/' in (temporary / 'robots.txt').read_bytes(), 'Existing preview assembler would change root robots.txt'
        temporary.rename(destination)
    finally:
        if temporary.exists(): shutil.rmtree(temporary)

def inventory(site, limit):
    site = Path(site); root_info = site.lstat()
    assert stat.S_ISDIR(root_info.st_mode) and not stat.S_ISLNK(root_info.st_mode)
    records = {'.':{'type':'directory','mode':stat.S_IMODE(root_info.st_mode)}}; total = 0
    for path in sorted(site.rglob('*')):
        info = path.lstat(); assert not stat.S_ISLNK(info.st_mode), 'Site symlink forbidden'
        assert stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode), 'Site special file forbidden'
        relative = path.relative_to(site)
        if path.is_file():
            total += info.st_size
            assert total <= limit, 'Whole-site original byte limit exceeded'
        if relative.parts[:2] == ('4d', 'dev'): continue
        records[relative.as_posix()] = ({'type':'file', 'bytes':info.st_size, 'sha256':digest_file(path), 'mode':stat.S_IMODE(info.st_mode)}
            if path.is_file() else {'type':'directory', 'mode':stat.S_IMODE(info.st_mode)})
    return {'nonDEV':records, 'whole_site_regular_bytes':total, 'site_limit_bytes':limit}

def compare(site, before, limit):
    after = inventory(site, limit)
    assert after['nonDEV'] == before['nonDEV'], 'A nonDEV file was added, removed, changed or chmodded'
    return {'status':'PASS_NONDEV_BYTES_MEMBERS_AND_MODES_UNCHANGED', 'nonDEV_files':len(after['nonDEV']),
            'whole_site_regular_bytes':after['whole_site_regular_bytes'], 'site_limit_bytes':limit,
            'reserve_bytes':limit-after['whole_site_regular_bytes']}

def validate_promotion_authority(run, jobs, receipt, expected_sha, owner):
    assert run['event'] == 'workflow_dispatch' and run['path'] == '.github/workflows/chicago-4d-promote-to-prod.yml'
    assert run['actor']['login'] == run['triggering_actor']['login'] == owner
    assert run['conclusion'] in (None, 'success') and run['status'] in ('in_progress','completed')
    assert receipt['run_id'] == run['id'] and receipt['actor'] == owner
    assert receipt['source_sha'] == run['head_sha'] and receipt['promoted_sha'] == expected_sha
    assert any(s['name'] == 'Merge dev into main, then open the back-merge as a PR' and s['conclusion'] == 'success'
               for j in jobs for s in j.get('steps',[])), 'Promotion merge has no actual passing step'

def api(path):
    return json.loads(subprocess.check_output(['gh','api','repos/kevinrhaas/chicago/'+path], stderr=subprocess.PIPE))

def cli():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['metadata','seed','snapshot','verify','promotion-authority','fresh-upload'])
    p.add_argument('--policy',default='.github/live-production.json');p.add_argument('--site',default='site')
    p.add_argument('--archive',default='baseline.zip');p.add_argument('--live-build',default='live-production-build.json')
    p.add_argument('--inventory',default='nonDEV-before.json');p.add_argument('--out',default='preservation-result.json')
    p.add_argument('--promotion-run');p.add_argument('--expected-sha');p.add_argument('--receipt')
    a=p.parse_args();policy=json.loads(Path(a.policy).read_bytes())
    if a.action=='metadata':
        run=api('actions/runs/'+str(policy['run_id']));artifacts=api('actions/runs/'+str(policy['run_id'])+'/artifacts')['artifacts']
        assert len(artifacts)==1, 'Ambiguous baseline artifacts'
        validate_baseline(policy,run,artifacts[0],json.loads(Path(a.live_build).read_bytes()))
        value={'baseline_run':policy['run_id'],'artifact':policy['artifact_id'],'status':'PASS_BASELINE_METADATA','artifact_digest':policy['artifact_digest']}
    elif a.action=='seed':
        seed_site(a.archive,a.site,policy,Path(a.live_build).read_bytes());value={'status':'PASS_EXACT_LIVE_BASELINE_SEEDED'}
    elif a.action=='snapshot':
        value=inventory(a.site,policy['site_limit_bytes']);Path(a.inventory).write_text(json.dumps(value,sort_keys=True)+'\n')
    elif a.action=='verify': value=compare(a.site,json.loads(Path(a.inventory).read_bytes()),policy['site_limit_bytes'])
    elif a.action=='promotion-authority':
        run=api('actions/runs/'+str(a.promotion_run));jobs=api('actions/runs/'+str(a.promotion_run)+'/jobs')['jobs']
        validate_promotion_authority(run,jobs,json.loads(Path(a.receipt).read_bytes()),a.expected_sha,policy['owner'])
        value={'status':'PASS_LINKED_OWNER_PROMOTION','promotion_run_id':run['id'],'promoted_sha':a.expected_sha}
    else:
        run=api('actions/runs/'+os.environ['GITHUB_RUN_ID'])
        assert run['run_attempt']==1, 'Use a fresh workflow run; do not rebuild/upload into a retry attempt'
        artifacts=api('actions/runs/'+os.environ['GITHUB_RUN_ID']+'/artifacts')['artifacts']
        assert not any(x['name']=='github-pages' for x in artifacts), 'This run already has a Pages artifact'
        value={'status':'PASS_ONE_FRESH_UPLOAD','run_id':run['id']}
    Path(a.out).write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))

if __name__=='__main__': cli()
