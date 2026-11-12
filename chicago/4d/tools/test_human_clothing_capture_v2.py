#!/usr/bin/env python3
"""Small metadata/injection/isolation controls; never invokes a producer."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import textwrap
import unittest
from unittest.mock import patch
import human_clothing_capture_v2 as C


class CaptureControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = self.root/'repo/chicago/4d'; self.app.mkdir(parents=True)
        required = ['tools/'+n for n in ('human_teamster_blend.py', 'human_export.py', 'human_export.sh', 'human_contract.py', 'human_skin_canonicalize.py', 'human_web_texture_inputs.py', 'web_derivatives.sh')]
        required += ['generators/blender.pin', 'data/humans/contract.json', C.FAMILIES[0][0], 'body.json']
        rows = []
        for name in required:
            p = self.app/name; p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b'canonical source\n')
            if name == C.FAMILIES[0][0]:
                p.write_text(json.dumps({'liberty': 'L418', 'proof_variants': [{'id': C.FAMILIES[0][1], 'component_assembly': C.FAMILIES[0][2], 'body_input': 'body.json'}]}))
            rows.append(dict(file=name, mode='100644', git_blob=C.blob(p.read_bytes())))
        self.doc = dict(basis_revision='a'*40, schema='t1789_clothing_capture_request_v2', status='SOURCE_ONLY_LINEN_CAPTURE_REQUEST',
                        release=False, install=False, native_fit_accepted=False, material_admission=None,
                        inputs=rows, families=[dict(zip(('recipe','variant','assembly','liberty'), C.FAMILIES[0]))])
        self.output = self.root/'external'

    def validate(self, doc=None, **overrides):
        raw = json.dumps(doc or self.doc).encode()
        args = dict(raw=raw, expected_hash=C.digest(raw), source='a'*40, actual='a'*40,
                    output=self.output, app=self.app)
        args.update(overrides)
        return C.validate_request(**args)

    def test_valid_capture_request_does_not_create_output(self):
        doc, out = self.validate()
        self.assertFalse(out.exists())
        self.assertFalse(doc['release'])
        self.assertIsNone(doc['material_admission'])

    def test_source_manifest_and_version_refusal(self):
        for values in ({'actual':'b'*40}, {'source':'main'}, {'expected_hash':'0'*64}, {'source':'b'*40,'actual':'b'*40}):
            with self.subTest(values=values), self.assertRaises(ValueError): self.validate(**values)
        for key, value in [('schema','v99'),('release',True),('install',True),('native_fit_accepted',True),('material_admission',{})]:
            d=copy.deepcopy(self.doc);d[key]=value
            with self.subTest(key=key), self.assertRaises(ValueError):self.validate(d)
        self.assertFalse(self.output.exists())

    def test_recipe_family_and_source_mutation_refusal(self):
        for key in ('recipe','variant','assembly','liberty'):
            d=copy.deepcopy(self.doc);d['families'][0][key]='unknown'
            with self.subTest(key=key), self.assertRaises(ValueError):self.validate(d)
        (self.app/'body.json').write_text('changed')
        with self.assertRaises(ValueError):self.validate()
        self.assertFalse(self.output.exists())

    def test_path_injection_symlinks_duplicates_and_modes_refused(self):
        for name in ('../escape','/tmp/escape','tools/./x','.git/config','x//y'):
            d=copy.deepcopy(self.doc);d['inputs'][0]['file']=name
            with self.subTest(name=name), self.assertRaises(ValueError):self.validate(d)
        d=copy.deepcopy(self.doc);d['inputs'].append(d['inputs'][0])
        with self.assertRaises(ValueError):self.validate(d)
        (self.app/'body.json').chmod(0o755)
        with self.assertRaises(ValueError):self.validate()
        (self.app/'body.json').unlink();(self.app/'body.json').symlink_to('/dev/null')
        with self.assertRaises(ValueError):self.validate()

    def test_output_isolation_and_inventory(self):
        for out in (self.app/'assets', self.app.parent/'x'):
            with self.subTest(out=out), self.assertRaises(ValueError):self.validate(output=out)
        self.output.mkdir()
        with self.assertRaises(ValueError):self.validate()
        (self.output/'x').write_bytes(b'actual')
        self.assertEqual(C.inventory(self.output)[0]['sha256'], hashlib.sha256(b'actual').hexdigest())
        (self.output/'link').symlink_to(self.output/'x')
        with self.assertRaises(ValueError):C.inventory(self.output)

    def test_exact_codec_arguments_all_four_lods_no_shell(self):
        for lod, cap in enumerate(('2048','1024','512','256')):
            commands=C.codec_commands(Path('literal $() ;/x.lod'+str(lod)+'.glb'),Path('dest'),Path('scratch'),['npx','gltf-transform'])
            self.assertTrue(all(isinstance(c,list) for c in commands))
            self.assertEqual(commands[1][-4:],['--width',cap,'--height',cap])
            self.assertEqual(commands[2][-8:],['--formats','*','--quality','92','--pattern','c4d_web_opaque_*','--slots','{baseColorTexture,emissiveTexture}'])
            self.assertEqual(commands[3][-6:],['--quantization-volume','scene','--level','medium','--quantize-normal','16'])
            self.assertIn('$()',commands[0][2])

    def test_closed_eight_family_missing_extra_and_link_refusal(self):
        parents=self.root/'parents';parents.mkdir();(parents/'web').mkdir()
        asset=C.FAMILIES[0][1]
        for prefix in ('','web/'):
            for lod in range(4):(parents/(prefix+asset+'.lod'+str(lod)+'.glb')).write_bytes(b'fixture only')
        self.assertEqual(len(C.parent_paths(parents,asset)),8)
        (parents/'extra').mkdir()
        with self.assertRaises(ValueError):C.parent_paths(parents,asset)
        (parents/'extra').rmdir()
        chosen=parents/(asset+'.lod0.glb');chosen.unlink()
        with self.assertRaises(ValueError):C.parent_paths(parents,asset)
        chosen.symlink_to('/dev/null')
        with self.assertRaises(ValueError):C.parent_paths(parents,asset)

    def test_run_preserves_argument_arrays_and_propagates_error_without_retry(self):
        import subprocess
        with patch.object(C.subprocess,'run',side_effect=subprocess.CalledProcessError(7,['producer'])) as native:
            with self.assertRaises(subprocess.CalledProcessError):C.run(['producer','literal $(x);'],log=self.root/'producer.log',app=self.app)
            self.assertEqual(native.call_count,1)
            self.assertEqual(native.call_args.args[0],['producer','literal $(x);'])
            self.assertNotIn('shell',native.call_args.kwargs)

    def test_master_uses_existing_adapter_without_relaxing_normal_guard(self):
        family = self.root/'normal-build'; family.mkdir()
        row = dict(zip(('recipe','variant','assembly','liberty'), C.FAMILIES[0]))
        def producer(command, **kwargs):
            self.assertIn('--experimental-normal-probes', command)
            self.assertNotIn('--normal-tolerance', command)
            temporary = Path(command[command.index('--normal-probe-receipts')+1])
            self.assertTrue(temporary.is_relative_to(Path('/tmp')))
            (temporary/'actual.json').write_text(json.dumps({
                'status':'passed', 'mesh_invariant_unchanged':True,
                'after':{'tolerance':1e-3,'maximum_raw_vector_delta':5.9e-5}}))
        with patch.object(C, 'run', side_effect=producer) as runner:
            C.build_master(Path('/never-executed'), row, family/'master.blend', family,
                           family/'producer.log', self.app)
            runner.assert_called_once()
        self.assertTrue((family/'normal-evidence/actual.json').is_file())

    def test_master_failure_retains_probe_diagnostics_and_does_not_retry(self):
        import subprocess
        family = self.root/'failed-normal-build'; family.mkdir()
        row = dict(zip(('recipe','variant','assembly','liberty'), C.FAMILIES[0]))
        def producer(command, **kwargs):
            temporary = Path(command[command.index('--normal-probe-receipts')+1])
            (temporary/'failure.json').write_text('{"status":"failed"}')
            raise subprocess.CalledProcessError(1, command)
        with patch.object(C, 'run', side_effect=producer) as runner:
            with self.assertRaises(subprocess.CalledProcessError):
                C.build_master(Path('/never-executed'), row, family/'master.blend', family,
                               family/'producer.log', self.app)
            runner.assert_called_once()
        self.assertEqual(json.loads((family/'normal-evidence/failure.json').read_text())['status'], 'failed')

    def fixture_binding(self, request_doc, expected_hash=None, definition='a'*40):
        workflow=(C.REPO/'.github/workflows/chicago-4d-humans.yml').read_text()
        section=workflow.split('- name: Bind fixture prerequisite to actual clothing source',1)[1]
        code=re.search(r"python3 - <<'PYCODE'\n(.*?)\n          PYCODE",section,re.S).group(1)
        owner=self.root/'_t1789_capture_owner/chicago/4d/data/humans/studies'
        owner.mkdir(parents=True);template=copy.deepcopy(self.doc);template['basis_revision']=None
        (owner/'clothing-capture-v2.json').write_text(json.dumps(template))
        raw=json.dumps(request_doc).encode()
        env=dict(EXPECTED_SOURCE='a'*40,EXPECTED_DEFINITION=definition,EXPECTED_MANIFEST=expected_hash or C.digest(raw),
                 DEFINITION_REF='reviewed/definition',RUNNER_TEMP=str(self.root),GITHUB_OUTPUT=str(self.root/'github-output'))
        def metadata_only(command,**kwargs):
            self.assertIn('--refresh-request',command)
            target=Path(command[command.index('--output')+1]);target.mkdir()
            (target/'clothing-capture-v2.json').write_bytes(raw)
        original=Path.cwd()
        try:
            os.chdir(self.root)
            with patch.dict(os.environ,env,clear=True),patch('subprocess.check_output',side_effect=['a'*40+'\n',definition+'\n']),patch('subprocess.run',side_effect=metadata_only) as runner:
                with self.assertRaises(SystemExit):exec(compile(textwrap.dedent(code),'actual-fixture-binding','exec'),{})
                self.assertLessEqual(runner.call_count,1)
        finally:os.chdir(original)
        self.assertLess(section.index('--refresh-request'),section.index('--preflight-only'))
        self.assertLess(section.index('--preflight-only'),section.index('run: ./tools/human_export.sh --verify'))

    def test_fixture_inline_wrong_basis_refuses_after_hash_before_producer(self):
        wrong=copy.deepcopy(self.doc);wrong['basis_revision']='b'*40
        self.fixture_binding(wrong)

    def test_fixture_inline_wrong_H_refuses_before_preflight_or_producer(self):
        self.fixture_binding(self.doc,expected_hash='0'*64)

    def test_fixture_inline_different_definition_refuses_before_refresh(self):
        self.fixture_binding(self.doc,definition='d'*40)

    def test_capture_job_inline_wrong_H_cannot_start_capture(self):
        workflow=(C.REPO/'.github/workflows/chicago-4d-humans.yml').read_text()
        section=workflow.split('- name: Capture canonical parents without active writes',1)[1]
        code=re.search(r"python3 - <<'PYCODE'\n(.*?)\n          PYCODE",section,re.S).group(1)
        target=self.root/'data/humans/studies';target.mkdir(parents=True)
        (target/'clothing-capture-v2.json').write_text(json.dumps(self.doc))
        env=dict(EXPECTED_SOURCE='a'*40,DEFINITION_SHA='a'*40,EXPECTED_MANIFEST='0'*64,
                 DEFINITION_REF='definition',GITHUB_WORKSPACE=str(self.root),RUNNER_TEMP=str(self.root))
        def only_refresh(command,**kwargs):
            self.assertIn('--refresh-request',command)
            target=Path(command[command.index('--output')+1]);target.mkdir()
            (target/'clothing-capture-v2.json').write_text(json.dumps(self.doc))
        original=Path.cwd()
        try:
            os.chdir(self.root)
            with patch.dict(os.environ,env,clear=True),patch('subprocess.run',side_effect=only_refresh) as runner:
                with self.assertRaises(SystemExit):exec(compile(textwrap.dedent(code),'actual-capture-job','exec'),{})
                self.assertEqual(runner.call_count,1)
        finally:os.chdir(original)

    def test_actual_preflight_validates_source_and_canonical_before_return(self):
        from types import SimpleNamespace
        driver=self.root/'driver/chicago/4d';driver.mkdir(parents=True)
        canonical=['generators/blender.pin']+['tools/'+n for n in ('human_teamster_blend.py','human_export.py','human_export.sh','human_skin_canonicalize.py','human_web_texture_inputs.py','web_derivatives.sh','human_contract.py')]
        for name in canonical:
            target=driver/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((self.app/name).read_bytes())
        for index in range(245-len(self.doc['inputs'])):
            name='tools/selected-%03d.py'%index;path=self.app/name;path.write_bytes(b'selected metadata fixture')
            self.doc['inputs'].append(dict(file=name,mode='100644',git_blob=C.blob(path.read_bytes())))
        raw=json.dumps(self.doc).encode();manifest=driver/C.MANIFEST;manifest.parent.mkdir(parents=True);manifest.write_bytes(raw)
        request=self.root/'reviewed-request.json';request.write_bytes(raw)
        args=SimpleNamespace(source_app=self.app,source='a'*40,definition_sha='a'*40,definition_ref='definition',manifest_sha256=C.digest(raw),output=self.output,preflight_only=True,request=request)
        def git_only(command,**kwargs):
            if command==['git','rev-parse','HEAD']:return 'a'*40
            if command==['git','rev-parse','--show-toplevel']:return str(self.app.parents[1])
            if command[:2]==['git','status']:return ''
            raise AssertionError('unexpected process in metadata preflight')
        with patch.object(C,'APP',driver),patch.object(C,'REPO',driver.parents[1]),patch.object(C,'run',side_effect=git_only),patch.object(C,'prepare_tools') as tools,patch.object(C,'source_snapshot') as snapshots:
            C.capture(args)
            tools.assert_not_called();snapshots.assert_not_called();self.assertFalse(self.output.exists())
            reduced=copy.deepcopy(self.doc);reduced['inputs']=reduced['inputs'][:-1]
            bad=json.dumps(reduced).encode();request.write_bytes(bad);args.manifest_sha256=C.digest(bad)
            with self.assertRaisesRegex(ValueError,'complete immutable template input set'):C.capture(args)
            request.write_bytes(raw);args.manifest_sha256=C.digest(raw)
            args.definition_sha='d'*40
            with self.assertRaisesRegex(ValueError,'same immutable commit'):C.capture(args)
            args.definition_sha='a'*40
            (driver/'tools/human_export.sh').write_text('changed shell owner')
            with self.assertRaises(ValueError):C.capture(args)
            tools.assert_not_called();snapshots.assert_not_called();self.assertFalse(self.output.exists())

    def test_real_settler_request_refuses_unknown_or_other_source_before_inputs(self):
        raw=(C.APP/C.MANIFEST).read_bytes();request=json.loads(raw)
        basis=request['basis_revision']
        if basis is None:
            self.assertEqual(request['status'],'SOURCE_ONLY_LINEN_BINDING_DRAFT_NOT_DISPATCHABLE')
        else:
            self.assertRegex(basis,r'^[0-9a-f]{40}$')
            self.assertEqual(request['status'],'SOURCE_ONLY_LINEN_CAPTURE_REQUEST')
        other='0'*40 if basis!='0'*40 else '1'*40
        with self.assertRaisesRegex(ValueError,'manifest basis'):
            C.validate_request(raw,C.digest(raw),other,other,self.output,app=self.app)
        self.assertFalse(self.output.exists())

    def refresh_context(self):
        from types import SimpleNamespace
        driver=self.root/'refresh-driver/chicago/4d';driver.mkdir(parents=True)
        canonical=['generators/blender.pin']+['tools/'+n for n in ('human_teamster_blend.py','human_export.py','human_export.sh','human_skin_canonicalize.py','human_web_texture_inputs.py','web_derivatives.sh','human_contract.py')]
        for name in canonical:
            target=driver/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((self.app/name).read_bytes())
        draft=copy.deepcopy(self.doc);draft['basis_revision']=None;draft['status']='SOURCE_ONLY_LINEN_BINDING_DRAFT_NOT_DISPATCHABLE'
        raw=json.dumps(draft).encode();manifest=driver/C.MANIFEST;manifest.parent.mkdir(parents=True);manifest.write_bytes(raw)
        args=SimpleNamespace(source_app=self.app,source='a'*40,definition_sha='a'*40,definition_ref='definition',manifest_sha256=C.digest(raw),output=self.output)
        tree=b''.join((r['mode']+' blob '+r['git_blob']+'\tchicago/4d/'+r['file']).encode()+b'\0' for r in draft['inputs'])
        def git_only(command,**kwargs):
            if command==['git','rev-parse','HEAD']:return 'a'*40
            if command==['git','rev-parse','--show-toplevel']:return str(self.app.parents[1])
            if command[:2]==['git','status']:return ''
            raise AssertionError('unexpected process in request refresh')
        return driver,args,tree,git_only

    def test_refresh_authors_real_tree_bound_external_request_only(self):
        driver,args,tree,git_only=self.refresh_context()
        with patch.object(C,'APP',driver),patch.object(C,'REPO',driver.parents[1]),patch.object(C,'run',side_effect=git_only),patch.object(C.subprocess,'check_output',return_value=tree),patch.object(C,'prepare_tools') as tools:
            C.refresh_request(args);tools.assert_not_called()
        refreshed=json.loads((self.output/'clothing-capture-v2.json').read_text())
        self.assertEqual(refreshed['basis_revision'],'a'*40)
        self.assertEqual(refreshed['status'],'SOURCE_ONLY_LINEN_CAPTURE_REQUEST')
        self.assertFalse(refreshed['release']);self.assertIsNone(refreshed['material_admission'])
        self.assertNotIn('outputs',refreshed)
        self.assertEqual(json.loads((driver/C.MANIFEST).read_text())['basis_revision'],None)
        self.assertEqual(json.loads((self.output/'REFRESH.json').read_text())['producer_run'],False)

    def test_refresh_H_is_deterministic_across_external_paths_and_run_metadata(self):
        driver,args,tree,git_only=self.refresh_context()
        with patch.object(C,'APP',driver),patch.object(C,'REPO',driver.parents[1]),patch.object(C,'run',side_effect=git_only),patch.object(C.subprocess,'check_output',return_value=tree),patch.object(C,'prepare_tools') as tools:
            with patch.dict(os.environ,{'GITHUB_RUN_ID':'101'}):C.refresh_request(args)
            first=(args.output/'clothing-capture-v2.json').read_bytes()
            args.output=self.root/'second-request';args.definition_ref='same commit through another ref'
            with patch.dict(os.environ,{'GITHUB_RUN_ID':'202'}):C.refresh_request(args)
            second=(args.output/'clothing-capture-v2.json').read_bytes()
            self.assertEqual(first,second);tools.assert_not_called()
            self.assertEqual(json.loads((args.output/'REFRESH.json').read_text())['workflow_run']['GITHUB_RUN_ID'],'202')
        self.assertNotIn('workflow_run',json.loads(first))

    def test_refresh_different_definition_rejects_before_tree_or_output(self):
        driver,args,tree,git_only=self.refresh_context();args.definition_sha='d'*40
        with patch.object(C,'APP',driver),patch.object(C,'REPO',driver.parents[1]),patch.object(C,'run',side_effect=git_only),patch.object(C.subprocess,'check_output') as tree_reader:
            with self.assertRaisesRegex(ValueError,'same immutable commit'):C.refresh_request(args)
            tree_reader.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_refresh_refuses_missing_source_tree_member_before_output(self):
        driver,args,tree,git_only=self.refresh_context()
        incomplete=b'\0'.join(tree.split(b'\0')[:-2])+b'\0'
        with patch.object(C,'APP',driver),patch.object(C,'REPO',driver.parents[1]),patch.object(C,'run',side_effect=git_only),patch.object(C.subprocess,'check_output',return_value=incomplete),patch.object(C,'prepare_tools') as tools:
            with self.assertRaises(ValueError):C.refresh_request(args)
            tools.assert_not_called()
        self.assertFalse(self.output.exists())

    def version_cache(self):
        cache = self.root/'fixture-provisioned-cache'; cache.mkdir()
        archive = cache/'blender-4.5.3-linux-x64.tar.xz'
        archive.write_bytes(b'small archive checksum control')
        binary = cache/'blender-4.5.3-linux-x64/blender'
        binary.parent.mkdir(); binary.write_bytes(b'not executed')
        (self.app/'generators/blender.pin').write_text(
            'BLENDER_VERSION=4.5.3\n'
            'BLENDER_DIR=blender-4.5.3-linux-x64\n'
            'BLENDER_URL=https://download.blender.org/release/Blender4.5/blender-4.5.3-linux-x64.tar.xz\n'
            'BLENDER_SHA256='+C.digest(archive.read_bytes())+'\n')
        # Exercise the actual canonical shell syntax rather than inventing pin lines.
        (self.app/'tools/web_derivatives.sh').write_bytes(
            (C.APP/'tools/web_derivatives.sh').read_bytes())
        return cache, archive, binary

    def test_verified_blender_cache_accepts_actual_LTS_header_only(self):
        cache, archive, binary = self.version_cache()
        with patch.object(C,'APP',self.app),patch.dict(os.environ,{'BLENDER_CACHE':str(cache)}):
            with patch.object(C,'run',return_value='Blender 4.5.3 LTS\nBuild date: fixture') as runner:
                actual, cli = C.prepare_tools()
                self.assertEqual(actual,binary)
                runner.assert_called_once_with([str(binary),'--version'])
                self.assertEqual(cli,['npx','--yes',
                    '--package','@gltf-transform/cli@4.5.0',
                    '--package','@gltf-transform/core@4.5.0',
                    '--package','@gltf-transform/functions@4.5.0',
                    '--package','@gltf-transform/extensions@4.5.0','gltf-transform'])
            for wrong in ('Blender 4.5.4 LTS','Blender 4.5.3','Blender 4.5.3 LTS unexpected',''):
                with self.subTest(header=wrong),patch.object(C,'run',return_value=wrong) as runner:
                    with self.assertRaises(ValueError) as error:C.prepare_tools()
                    self.assertIn('pinned Blender version',str(error.exception))
                    self.assertIn('observed '+repr(wrong),str(error.exception))
                    runner.assert_called_once_with([str(binary),'--version'])

    def test_LTS_header_cannot_bypass_archive_checksum(self):
        cache, archive, binary = self.version_cache()
        archive.write_bytes(b'corrupted archive')
        with patch.object(C,'APP',self.app),patch.dict(os.environ,{'BLENDER_CACHE':str(cache)}),patch.object(C,'run',return_value='Blender 4.5.3 LTS') as runner:
            with self.assertRaisesRegex(ValueError,'pinned Blender archive checksum'):C.prepare_tools()
            runner.assert_not_called()

    def test_real_codec_pin_syntax_refuses_changed_missing_ambiguous_and_shell_values(self):
        cache, archive, binary = self.version_cache()
        path = self.app/'tools/web_derivatives.sh'; actual = path.read_text()
        canonical = 'GT_CLI_VERSION="4.5.0"'
        self.assertEqual(actual.count(canonical),1)
        marker = self.root/'must-not-be-created'
        cases = {
            'wrong-version': actual.replace(canonical,'GT_CLI_VERSION="4.5.1"'),
            'missing': actual.replace(canonical+'\n',''),
            'ambiguous': actual+'\n'+canonical+'\n',
            'shell-suffix': actual.replace(canonical,canonical+'; touch '+str(marker)),
            'shell-substitution': actual.replace(canonical,'GT_CLI_VERSION="$(touch '+str(marker)+')"'),
            'unquoted': actual.replace(canonical,'GT_CLI_VERSION=4.5.0'),
        }
        with patch.object(C,'APP',self.app),patch.dict(os.environ,{'BLENDER_CACHE':str(cache)}):
            for name, text in cases.items():
                path.write_text(text)
                with self.subTest(case=name),patch.object(C,'run',return_value='Blender 4.5.3 LTS') as runner:
                    with self.assertRaisesRegex(ValueError,'exact existing codec closure'):C.prepare_tools()
                    runner.assert_called_once_with([str(binary),'--version'])
                    self.assertFalse(marker.exists())

    def execute_args(self):
        from types import SimpleNamespace
        return SimpleNamespace(source='a'*40,definition_sha='a'*40,definition_ref='reviewed-definition',manifest_sha256='f'*64)

    def test_initial_incomplete_receipt_precedes_fake_producer_interruption(self):
        def interrupted(args,**kwargs):
            persisted=json.loads((self.output/'CAPTURE.json').read_text())
            self.assertEqual(persisted['status'],'INCOMPLETE')
            self.assertEqual(persisted['phase'],'PRODUCERS')
            self.assertEqual(persisted['source_sha'],'a'*40)
            self.assertFalse(persisted['release']);self.assertFalse(persisted['install'])
            self.assertEqual(persisted['workflow_run'],C.workflow_lineage())
            self.assertEqual(persisted['request_template_sha256'],C.digest((C.APP/C.MANIFEST).read_bytes()))
            (self.output/'owned-partial.bin').write_bytes(b'partial')
            raise KeyboardInterrupt('owned fake producer interruption')
        with patch.object(C,'source_snapshot',return_value=('actual-hash',1)),patch.object(C,'prepare_tools',return_value=(Path('/never-executed-blender'),['pinned-cli'])),patch.object(C,'run',side_effect=interrupted) as runner:
            with self.assertRaises(KeyboardInterrupt):C.execute_capture(self.execute_args(),self.doc,self.output,self.app,'a'*40,'a'*40,[])
            self.assertEqual(runner.call_count,1)
        final=json.loads((self.output/'CAPTURE.json').read_text())
        self.assertEqual(final['status'],'INCOMPLETE');self.assertFalse(final['release'])
        self.assertIn('KeyboardInterrupt',final['error']);self.assertTrue((self.output/'owned-partial.bin').exists())
        self.assertNotIn('CAPTURE.json',[r['file'] for r in final['files']])

    def test_post_admission_cache_failure_retains_lineage_and_no_producer(self):
        with patch.object(C,'source_snapshot',return_value=('actual-hash',1)),patch.object(C,'prepare_tools',side_effect=ValueError('missing fixture cache')),patch.object(C,'run') as runner:
            with self.assertRaises(ValueError):C.execute_capture(self.execute_args(),self.doc,self.output,self.app,'a'*40,'a'*40,[])
            runner.assert_not_called()
        final=json.loads((self.output/'CAPTURE.json').read_text())
        self.assertEqual(final['status'],'INCOMPLETE');self.assertFalse(final['release'])
        self.assertEqual(final['driver_sha'],'a'*40);self.assertIn('missing fixture cache',final['error'])

    def test_closing_failure_cannot_leave_complete_status(self):
        with patch.object(C,'source_snapshot',side_effect=[('before',1),('before',1),OSError('closing hash unavailable')]),patch.object(C,'prepare_tools',side_effect=ValueError('cache failure')):
            with self.assertRaises(ValueError):C.execute_capture(self.execute_args(),self.doc,self.output,self.app,'a'*40,'a'*40,[])
        final=json.loads((self.output/'CAPTURE.json').read_text())
        self.assertEqual(final['status'],'INCOMPLETE_CLOSING_PROOF');self.assertFalse(final['release'])
        self.assertIn('closing hash unavailable',final['closing_error'])

    def mode_validation(self, **env):
        workflow=(C.REPO/'.github/workflows/chicago-4d-humans.yml').read_text()
        section=workflow.split('- name: Validate opt-in study request before checkout',1)[1]
        source=re.search(r"python3 - <<'PY'\n(.*?)\n          PY",section,re.S).group(1)
        values=dict(SOURCE_REF='',DRESS_ENABLED='false',TEAMSTERS_ENABLED='false',SEATED_ENABLED='false',
                    CLOTHING_ENABLED='false',CLOTHING_SOURCE='',CLOTHING_MANIFEST='',STILLS_ENABLED='false',LIBRARY_SOURCE_RUN='',
                    PRAIRIE_ENABLED='false',
                    GITHUB_OUTPUT=str(self.root/'github-output'))
        values.update(env)
        with patch.dict(os.environ,values,clear=True):exec(compile(textwrap.dedent(source),'actual-workflow-mode-validation','exec'),{})

    def test_actual_workflow_modes_and_injection_refusal(self):
        self.mode_validation()
        self.mode_validation(DRESS_ENABLED='true',SOURCE_REF='1cbb1817508593562f99ed378b6932368b5699b9')
        self.mode_validation(CLOTHING_ENABLED='true',CLOTHING_SOURCE='a'*40,CLOTHING_MANIFEST='b'*64)
        self.mode_validation(PRAIRIE_ENABLED='true')
        for key in ('DRESS_ENABLED','TEAMSTERS_ENABLED','SEATED_ENABLED','STILLS_ENABLED','PRAIRIE_ENABLED'):
            with self.subTest(key=key),self.assertRaises(SystemExit):
                self.mode_validation(CLOTHING_ENABLED='true',CLOTHING_SOURCE='a'*40,CLOTHING_MANIFEST='b'*64,**{key:'true'})
        for key in ('DRESS_ENABLED','TEAMSTERS_ENABLED','SEATED_ENABLED','STILLS_ENABLED'):
            with self.subTest(prairie_conflict=key), self.assertRaises(SystemExit):
                self.mode_validation(PRAIRIE_ENABLED='true', **{key:'true'})
        for values in ({'CLOTHING_SOURCE':'a'*40},{'CLOTHING_MANIFEST':'b'*64},
                       {'CLOTHING_ENABLED':'true','CLOTHING_SOURCE':'$(touch /tmp/NO)','CLOTHING_MANIFEST':'b'*64},
                       {'SOURCE_REF':'a'*40},{'DRESS_ENABLED':'true','SOURCE_REF':'a'*40}):
            with self.subTest(values=values),self.assertRaises(SystemExit):self.mode_validation(**values)

    def test_workflow_read_only_no_promotion_and_default_inert(self):
        workflow=(C.REPO/'.github/workflows/chicago-4d-humans.yml').read_text()
        job=workflow.split('\n  clothing-capture-v2:\n',1)[1]
        self.assertIn("if: github.event_name == 'workflow_dispatch' && inputs.build_clothing_capture_v2",job)
        self.assertIn('contents: read',job)
        self.assertIn('needs: humans',job)
        humans=workflow.split('  humans:\n',1)[1].split('    runs-on:',1)[0]
        self.assertIn('|| inputs.clothing_source_ref || inputs.clothing_manifest_sha256',humans)
        self.assertIn('inputs.render_library_stills && !inputs.build_clothing_capture_v2 && !inputs.clothing_source_ref && !inputs.clothing_manifest_sha256',workflow)
        self.assertIn('persist-credentials: false',job)
        self.assertIn('path: capture-source',job)
        self.assertIn('path: capture-driver',job)
        self.assertIn('ref: ${{ github.workflow_sha }}',job)
        self.assertIn('--source-app',job)
        self.assertIn('if-no-files-found: error',job)
        for forbidden in ('git push','gh pr','deploy','contents: write','pull-requests: write','human_export.sh','human_charles_coat.py'):
            self.assertNotIn(forbidden,job)


if __name__ == '__main__': unittest.main()
