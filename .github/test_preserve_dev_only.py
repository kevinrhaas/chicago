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
        artifact={'id':policy['artifact_id'],'name':'github-pages','expired':False,'size_in_bytes':policy['artifact_zip_bytes'],'digest':policy['artifact_digest']};live={'version':'9c65defae'}
        guard.validate_baseline(policy,run,artifact,live)
        for subject,key,value in [('run','head_sha','ed676263'),('run','conclusion','failure'),('artifact','expired',True),('artifact','digest','sha256:wrong'),('live','version','ed676263')]:
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
    def step_script(self, name):
        lines=(BASE/'workflows/deploy.yml').read_text().splitlines()
        start=lines.index('      - name: '+name)
        end=next((i for i in range(start+1,len(lines)) if lines[i].startswith('      - ')),len(lines))
        block=lines[start:end];run=block.index('        run: |')
        body=[]
        for line in block[run+1:]:
            if line.strip() and not line.startswith('          '):break
            body.append(line[10:] if line else '')
        return '\n'.join(body)
    def test_actual_delivery_expression_defaults_push_and_dispatch_to_dev(self):
        text=(BASE/'workflows/deploy.yml').read_text()
        expression=re.search(r'DELIVERY_MODE: \$\{\{ (.*?) \}\}',text)[1]
        runner="const f=Function('github','inputs','return '+process.argv[1]); process.stdout.write(f(JSON.parse(process.argv[2]),JSON.parse(process.argv[3])));"
        for event,inputs,expected in [('push',{},'dev'),('push',{'mode':'production'},'dev'),('workflow_dispatch',{},'dev'),('workflow_dispatch',{'mode':'dev'},'dev'),('workflow_dispatch',{'mode':'production'},'production')]:
            with self.subTest(event=event,inputs=inputs):
                result=subprocess.check_output([shutil.which('node'),'-e',runner,expression,json.dumps({'event_name':event}),json.dumps(inputs)],text=True)
                self.assertEqual(result,expected)
        self.assertIn('default: dev',text)
        self.assertIn('group: pages\n  cancel-in-progress: false',text)
    def assembly(self, failure):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);bin_dir=root/'bin';bin_dir.mkdir();tools=root/'_dev-src/chicago/4d/tools';tools.mkdir(parents=True)
            (root/'site/4d/dev/packs').mkdir(parents=True)
            (tools/'publish.sh').write_text('test "$FAILURE" != publish\n')
            (tools/'write_year_packs.mjs').write_text('// fixture owning CLI marker\n')
            (bin_dir/'git').write_text('#!/bin/sh\ncase "$1" in\nfetch) test "$FAILURE" != fetch;;\nrev-parse) echo 0e7803553;;\nshow) echo 2026-11-10T21:47:00Z;;\nworktree) exit 0;;\nesac\n')
            (bin_dir/'node').write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$CALLS"\ncase "$*" in *--check*) test "$FAILURE" != packs;; *) exit 0;; esac\n')
            for p in bin_dir.iterdir():p.chmod(0o755)
            env=dict(os.environ,PATH=str(bin_dir)+os.pathsep+os.environ['PATH'],FAILURE=failure,DELIVERY_MODE='dev',CALLS=str(root/'calls'))
            result=subprocess.run(['bash','-e','-o','pipefail','-c',self.step_script('Assemble the 4D dev preview (no-op until the dev ref exists)')],cwd=root,env=env,capture_output=True,text=True)
            calls=(root/'calls').read_text() if (root/'calls').exists() else ''
            return result,calls
    def test_dev_fetch_failure_refuses_stale_seed_before_assembler(self):
        result,calls=self.assembly('fetch');self.assertNotEqual(result.returncode,0);self.assertEqual(calls,'')
    def test_dev_publish_failure_refuses_partial_preview_before_assembler(self):
        result,calls=self.assembly('publish');self.assertNotEqual(result.returncode,0);self.assertEqual(calls,'')
    def test_dev_pack_failure_is_fatal(self):
        result,calls=self.assembly('packs');self.assertNotEqual(result.returncode,0);self.assertIn('--check',calls)
    def test_complete_dev_assembly_runs_the_owner_check(self):
        result,calls=self.assembly('none');self.assertEqual(result.returncode,0,result.stderr);self.assertIn('--check',calls)

if __name__=='__main__':unittest.main(verbosity=2)
