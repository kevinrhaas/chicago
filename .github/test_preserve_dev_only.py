from pathlib import Path
import copy, hashlib, importlib.util, io, json, os, re, shutil, subprocess, tarfile, tempfile, unittest, zipfile

BASE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('guard',BASE/'preserve_dev_only.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)

class Preservation(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.site=self.root/'site';self.site.mkdir();(self.site/'4d/dev').mkdir(parents=True)
        (self.site/'4d/build.json').write_text('{"version":"9c65defae"}\n');(self.site/'robots.txt').write_text('User-agent: *\nDisallow: /4d/dev/\n')
        (self.site/'4d/dev/build.json').write_text('old DEV');self.before=guard.inventory(self.site,10000)
    def test_only_dev_content_can_change(self):
        (self.site/'4d/dev/build.json').write_text('new DEV');(self.site/'4d/dev/new.js').write_text('visible DEV change')
        self.assertEqual(guard.compare(self.site,self.before,10000)['status'],'PASS_NONDEV_BYTES_MEMBERS_AND_MODES_UNCHANGED')
    def test_production_byte_addition_deletion_and_mode_changes_refused(self):
        for variant in ['change','add','delete','mode']:
            with self.subTest(variant=variant):
                p=self.site/'4d/build.json';original=p.read_bytes();mode=p.stat().st_mode&0o777
                if variant=='change':p.write_bytes(b'new production')
                if variant=='add':(self.site/'outside.js').write_text('new')
                if variant=='delete':p.unlink()
                if variant=='mode':p.chmod(mode^0o100)
                with self.assertRaises(AssertionError):guard.compare(self.site,self.before,10000)
                p.write_bytes(original);p.chmod(mode);(self.site/'outside.js').unlink(missing_ok=True)
    def test_similar_prefix_is_not_dev_scope(self):
        (self.site/'4d/developer.txt').write_text('unrelated')
        with self.assertRaises(AssertionError):guard.compare(self.site,self.before,10000)
    def test_empty_nondev_directory_member_and_mode_are_protected(self):
        directory=self.site/'empty';directory.mkdir();before=guard.inventory(self.site,10000)
        directory.rmdir()
        with self.assertRaises(AssertionError):guard.compare(self.site,before,10000)
        directory.mkdir();mode=directory.stat().st_mode&0o777;directory.chmod(mode^0o020)
        with self.assertRaises(AssertionError):guard.compare(self.site,before,10000)
    def test_site_root_mode_is_protected(self):
        mode=self.site.stat().st_mode&0o777;self.site.chmod(mode^0o020)
        with self.assertRaises(AssertionError):guard.compare(self.site,self.before,10000)
    def test_symlink_is_refused_even_in_dev(self):
        (self.site/'4d/dev/escape').symlink_to(self.site/'4d/build.json')
        with self.assertRaises(AssertionError):guard.compare(self.site,self.before,10000)
    def test_whole_site_original_byte_boundary(self):
        total=self.before['whole_site_regular_bytes'];guard.inventory(self.site,total)
        with self.assertRaises(AssertionError):guard.inventory(self.site,total-1)
    def archive(self, extra=None, link=False):
        tar_bytes=io.BytesIO()
        with tarfile.open(fileobj=tar_bytes,mode='w') as tar:
            entry=tarfile.TarInfo('.');entry.type=tarfile.DIRTYPE;entry.mode=0o750;tar.addfile(entry)
            for path in ['4d/build.json','robots.txt']:
                b=(self.site/path).read_bytes();entry=tarfile.TarInfo(path);entry.size=len(b);entry.mode=0o644;tar.addfile(entry,io.BytesIO(b))
            if extra:
                entry=tarfile.TarInfo(extra);entry.size=0
                if link:entry.type=tarfile.SYMTYPE;entry.linkname='/tmp'
                tar.addfile(entry,io.BytesIO())
        archive=self.root/'baseline.zip'
        with zipfile.ZipFile(archive,'w') as z:z.writestr('artifact.tar',tar_bytes.getvalue())
        return archive,{'artifact_zip_bytes':archive.stat().st_size,'artifact_digest':'sha256:'+guard.digest_file(archive),'site_limit_bytes':10000}
    def test_seed_is_byte_exact_and_live_marker_bound(self):
        archive,policy=self.archive();dest=self.root/'seed';live=(self.site/'4d/build.json').read_bytes();guard.seed_site(archive,dest,policy,live)
        self.assertEqual((dest/'4d/build.json').read_bytes(),live)
        self.assertEqual(dest.stat().st_mode&0o777,0o750)
        with self.assertRaises(AssertionError):guard.seed_site(archive,self.root/'wrong',policy,b'wrong live marker')
        self.assertFalse((self.root/'wrong').exists())
    def test_traversal_and_archive_links_refused_before_publish(self):
        for path,link in [('../escape',False),('/absolute',False),('4d/link',True)]:
            with self.subTest(path=path):
                archive,policy=self.archive(path,link)
                with self.assertRaises(AssertionError):guard.seed_site(archive,self.root/'bad',policy,(self.site/'4d/build.json').read_bytes())
                self.assertFalse((self.root/'bad').exists())
    def test_tampered_archive_is_refused(self):
        archive,policy=self.archive();archive.write_bytes(archive.read_bytes()+b'changed')
        with self.assertRaises(AssertionError):guard.seed_site(archive,self.root/'bad',policy,(self.site/'4d/build.json').read_bytes())
    def test_baseline_wrong_run_head_expiry_and_live_version_refused(self):
        policy=json.loads((BASE/'live-production.json').read_bytes())
        run={'id':policy['run_id'],'head_sha':policy['production_sha'],'head_branch':'main','conclusion':'success','status':'completed'}
        artifact={'id':policy['artifact_id'],'name':'github-pages','expired':False,'size_in_bytes':policy['artifact_zip_bytes'],'digest':policy['artifact_digest']};live={'version':policy['production_sha'][:9]}
        guard.validate_baseline(policy,run,artifact,live)
        for subject,key,value in [('run','head_sha','ed676263'),('run','conclusion','failure'),('artifact','expired',True),('artifact','digest','sha256:wrong'),('live','version','000000000')]:
            r,a,l=copy.deepcopy(run),copy.deepcopy(artifact),copy.deepcopy(live);{'run':r,'artifact':a,'live':l}[subject][key]=value
            with self.assertRaises(AssertionError):guard.validate_baseline(policy,r,a,l)
    def test_production_requires_matching_actual_owner_promotion(self):
        run={'id':7,'event':'workflow_dispatch','path':'.github/workflows/chicago-4d-promote-to-prod.yml','actor':{'login':'kevinrhaas'},'triggering_actor':{'login':'kevinrhaas'},'conclusion':None,'status':'in_progress','head_sha':'source'}
        jobs=[{'steps':[{'name':'Merge dev into main, then open the back-merge as a PR','conclusion':'success'}]}];receipt={'run_id':7,'actor':'kevinrhaas','source_sha':'source','promoted_sha':'promoted'}
        guard.validate_promotion_authority(run,jobs,receipt,'promoted','kevinrhaas')
        for change in ['actor','event','receipt','merge']:
            r,j,c=copy.deepcopy(run),copy.deepcopy(jobs),copy.deepcopy(receipt)
            if change=='actor':r['actor']['login']='github-actions[bot]'
            if change=='event':r['event']='push'
            if change=='receipt':c['promoted_sha']='another-main'
            if change=='merge':j[0]['steps'][0]['conclusion']='failure'
            with self.assertRaises(AssertionError):guard.validate_promotion_authority(r,j,c,'promoted','kevinrhaas')

class WorkflowPaths(unittest.TestCase):
    """Since 2026-11-13 the dev preview is kevinrhaas/chicago-dev's own Pages site.
    This site holds production only, deployed only for an owner promotion."""
    def text(self):
        return (BASE/'workflows/deploy.yml').read_text()
    def job_if(self, job):
        lines=self.text().splitlines();start=lines.index('  '+job+':')
        return next(l.split('if: ',1)[1] for l in lines[start+1:start+12] if l.startswith('    if: '))
    def evaluate(self, expression, github, inputs):
        runner="const f=Function('github','inputs','return '+process.argv[1]); process.stdout.write(String(f(JSON.parse(process.argv[2]),JSON.parse(process.argv[3]))));"
        js=expression.replace("'","\"")
        return subprocess.check_output([shutil.which('node'),'-e',runner,js,json.dumps(github),json.dumps(inputs)],text=True)
    def test_only_an_owner_promotion_deploys(self):
        expression=self.job_if('deploy')
        for github,inputs,expected in [
            ({'ref':'refs/heads/main','event_name':'push'},{},'false'),
            ({'ref':'refs/heads/main','event_name':'workflow_dispatch'},{},'false'),
            ({'ref':'refs/heads/main','event_name':'workflow_dispatch'},{'mode':'dev'},'false'),
            ({'ref':'refs/heads/dev','event_name':'workflow_dispatch'},{'mode':'production'},'false'),
            ({'ref':'refs/heads/dev','event_name':'push'},{},'false'),
            ({'ref':'refs/heads/main','event_name':'workflow_dispatch'},{'mode':'production'},'true')]:
            with self.subTest(github=github,inputs=inputs):
                self.assertEqual(self.evaluate(expression,github,inputs),expected)
        self.assertIn('group: pages\n  cancel-in-progress: false',self.text())
    def test_a_dev_push_dispatches_the_preview_site_and_never_fails(self):
        expression=self.job_if('refresh-previews')
        self.assertEqual(self.evaluate(expression,{'ref':'refs/heads/dev','event_name':'push'},{}),'true')
        self.assertEqual(self.evaluate(expression,{'ref':'refs/heads/main','event_name':'push'},{}),'false')
        text=self.text()
        self.assertIn('gh workflow run deploy-dev-preview.yml --repo kevinrhaas/chicago-dev',text)
        self.assertIn("|| echo \"::warning::dispatch to kevinrhaas/chicago-dev failed",text)
    def test_production_artifact_no_longer_assembles_a_preview(self):
        text=self.text()
        for gone in ['chicago-4d-dev-preview.mjs _dev-src','Seed exact live production','preview-root site/4d/dev']:
            self.assertNotIn(gone,text)
        self.assertIn('node .github/chicago-4d-dev-redirect.mjs site',text)
    def test_redirect_pages(self):
        with tempfile.TemporaryDirectory() as name:
            site=Path(name)/'site';(site/'4d/1835').mkdir(parents=True);(site/'4d/walk').mkdir()
            subprocess.run([shutil.which('node'),str(BASE/'chicago-4d-dev-redirect.mjs'),str(site)],check=True,capture_output=True)
            for rel in ['4d/dev/index.html','4d/dev/1835/index.html','4d/dev/walk/index.html','404.html']:
                page=(site/rel).read_text()
                self.assertIn('data-c4d-dev-moved',page);self.assertIn('https://dev.chicago.polecat.live',page)
            self.assertIn('unregister()',(site/'4d/dev/sw.js').read_text())
            self.assertFalse((site/'4d/dev/build.json').exists())
            (site/'404.html').write_text('own page')
            subprocess.run([shutil.which('node'),str(BASE/'chicago-4d-dev-redirect.mjs'),str(site)],check=True,capture_output=True)
            self.assertEqual((site/'404.html').read_text(),'own page')

if __name__=='__main__':unittest.main(verbosity=2)
