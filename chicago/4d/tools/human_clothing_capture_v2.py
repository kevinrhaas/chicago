#!/usr/bin/env python3
"""T1789 artifact-only canonical parent capture. No material admission or installer."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

APP = Path(__file__).resolve().parents[1]
REPO = APP.parents[1]
MANIFEST = 'data/humans/studies/clothing-capture-v2.json'
# Finite first increment only. Shared apron/collar/coachman bundle remains deferred.
FAMILIES = [('data/humans/recipes/settler_1812.json',
             'settler_1812', 'settler_1812_v1', 'L418')]
HEX40 = re.compile(r'[0-9a-f]{40}')
HEX64 = re.compile(r'[0-9a-f]{64}')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def relative(name):
    need(isinstance(name, str), "input path must be text")
    p = Path(name)
    need(isinstance(name, str) and not p.is_absolute() and name == p.as_posix()
         and '..' not in p.parts and p.parts and p.parts[0] != '.git', 'unsafe input path')
    return p


def run(args, *, log=None, app=APP):
    if log is None:
        return subprocess.check_output(args, cwd=app, text=True).strip()
    with log.open('ab') as stream:
        stream.write((json.dumps(args)+'\n').encode())
        subprocess.run(args, cwd=app, stdout=stream, stderr=subprocess.STDOUT, check=True)


def file_facts(path):
    size = path.stat().st_size
    sha256 = hashlib.sha256()
    git = hashlib.sha1(b'blob '+str(size).encode()+b'\0')
    with path.open('rb') as stream:
        while chunk := stream.read(1024*1024):
            sha256.update(chunk); git.update(chunk)
    return dict(bytes=size, sha256=sha256.hexdigest(), git_blob=git.hexdigest())


def source_snapshot(app=APP):
    repo = app.parents[1]
    names = subprocess.check_output(['git', 'ls-files', '-z', '--', 'chicago/4d'], cwd=repo).split(b'\0')
    rows = []
    for name in names:
        if not name:
            continue
        path = repo/os.fsdecode(name)
        need(path.is_file() or path.is_symlink(), 'tracked APP input missing')
        facts = dict(bytes=len(os.fsencode(os.readlink(path))), sha256=digest(os.fsencode(os.readlink(path)))) if path.is_symlink() else file_facts(path)
        rows.append((os.fsdecode(name), 'link' if path.is_symlink() else oct(path.stat().st_mode & 0o777), facts['bytes'], facts['sha256']))
    return digest(json.dumps(rows, separators=(',', ':')).encode()), len(rows)


def validate_request(raw, expected_hash, source, actual, output, app=APP, input_names=None):
    need(HEX40.fullmatch(source) and source == actual, 'exact reviewed checkout required')
    need(HEX64.fullmatch(expected_hash) and digest(raw) == expected_hash, 'reviewed manifest hash')
    output = Path(output).resolve()
    need(not output.exists() and not output.is_relative_to(app.resolve().parents[1]), 'fresh external output only')
    doc = json.loads(raw)
    need(doc.get('basis_revision') == source == actual, 'manifest basis must equal requested actual source before any producer')
    need(doc['schema'] == 't1789_clothing_capture_request_v2'
         and doc['status'] == 'SOURCE_ONLY_LINEN_CAPTURE_REQUEST', 'known capture request version')
    need(doc['release'] is False and doc['install'] is False
         and doc['native_fit_accepted'] is False and doc['material_admission'] is None, 'capture cannot admit assets')
    need([tuple(row[k] for k in ('recipe', 'variant', 'assembly', 'liberty')) for row in doc['families']] == FAMILIES,
         'only the reviewed finite T1789 family set')
    need(doc['inputs'] and len(doc['inputs']) <= 512, 'bounded source inventory')
    if input_names is not None:
        need(len(doc['inputs']) == len(input_names) and {r['file'] for r in doc['inputs']} == set(input_names), 'external request must retain the complete immutable template input set')
    names = set()
    for row in doc['inputs']:
        name = row['file']; relative(name)
        need(name not in names and HEX40.fullmatch(row['git_blob']) and row['mode'] in ('100644', '100755'), 'unique regular source binding')
        names.add(name)
        path = app/relative(name)
        need(path.is_file() and not path.is_symlink(), 'regular physical source input')
        need(file_facts(path)['git_blob'] == row['git_blob'], 'source input differs: '+name)
        need(bool(path.stat().st_mode & 0o111) == (row['mode'] == '100755'), 'source mode differs: '+name)
    required = {'tools/'+n for n in ('human_teamster_blend.py', 'human_export.py', 'human_export.sh', 'human_contract.py', 'human_skin_canonicalize.py', 'human_web_texture_inputs.py', 'web_derivatives.sh')}
    need(required | {'generators/blender.pin', 'data/humans/contract.json', FAMILIES[0][0]} <= names, 'required selected canonical inputs missing')
    for family in doc['families']:
        recipe = json.loads((app/family['recipe']).read_bytes())
        variants = [v for v in recipe['proof_variants'] if v['id'] == family['variant']]
        need(len(variants) == 1 and variants[0]['component_assembly'] == family['assembly']
             and recipe['liberty'] == family['liberty'], 'recipe/variant/assembly/liberty identity')
        need(variants[0]['body_input'] in names, 'bound actual body input')
    return doc, output


def codec_commands(master, target, scratch, cli):
    lod = int(master.name[-5])
    need(lod in range(4), 'four canonical LODs only')
    labeled, resized, color = [scratch/(n+'.glb') for n in ('labeled', 'resized', 'color')]
    cap = str((2048, 1024, 512, 256)[lod])
    return [['python3', 'tools/human_web_texture_inputs.py', str(master), str(labeled)],
            cli+['resize', str(labeled), str(resized), '--width', cap, '--height', cap],
            cli+['jpeg', str(resized), str(color), '--formats', '*', '--quality', '92', '--pattern', 'c4d_web_opaque_*', '--slots', '{baseColorTexture,emissiveTexture}'],
            cli+['meshopt', str(color), str(target), '--quantization-volume', 'scene', '--level', 'medium', '--quantize-normal', '16']]


def inventory(root, omit=()):
    rows = []
    for path in sorted(root.rglob('*')):
        need(not path.is_symlink(), 'artifact symlink refused')
        if path.is_file() and path.relative_to(root).as_posix() not in omit:
            rows.append(dict(file=path.relative_to(root).as_posix(), **file_facts(path)))
    return rows


def parent_paths(parents, asset):
    expected = {prefix+asset+'.lod'+str(lod)+'.glb' for prefix in ('', 'web/') for lod in range(4)}
    actual = {p.relative_to(parents).as_posix() for p in parents.rglob('*')}
    need(actual == expected | {'web'}, 'complete canonical eight-family only')
    need(all((parents/p).is_file() and not (parents/p).is_symlink() for p in expected)
         and (parents/'web').is_dir() and not (parents/'web').is_symlink(), 'regular canonical parents only')
    return sorted(expected)


def glb_metadata(path):
    import struct
    with path.open('rb') as stream:
        header = stream.read(20)
        need(len(header) == 20, 'GLB header')
        magic, version, length, size, kind = struct.unpack('<5I', header)
        need(magic == 0x46546c67 and version == 2 and length == path.stat().st_size
             and kind == 0x4e4f534a and 0 < size <= 16*1024*1024, 'bounded GLB2 JSON')
        raw = stream.read(size); need(len(raw) == size, 'complete GLB JSON')
    doc = json.loads(raw)
    return dict(json_sha256=digest(raw), scene_provenance=[s.get('extras', {}) for s in doc.get('scenes', [])],
                skins=[dict(joints=s.get('joints'), inverseBindMatrices=s.get('inverseBindMatrices')) for s in doc.get('skins', [])],
                animations=[dict(name=a.get('name'), channels=len(a.get('channels', [])),
                    input_domains=[dict(min=doc['accessors'][s['input']].get('min'), max=doc['accessors'][s['input']].get('max')) for s in a.get('samplers', [])]) for a in doc.get('animations', [])])


def prepare_tools():
    pin = (APP/'generators/blender.pin').read_text()
    values = dict(re.findall(r'^(BLENDER_[A-Z0-9_]+)=(\S+)$', pin, re.M))
    need(values['BLENDER_VERSION'] == '4.5.3', 'existing Blender pin')
    cache = Path(os.environ.get('BLENDER_CACHE', '/opt/blender-dl'))
    binary = cache/values['BLENDER_DIR']/'blender'
    archive = cache/values['BLENDER_URL'].split('/')[-1]
    need(binary.is_file() and archive.is_file(), 'fixture-provisioned verified Blender cache required; capture never installs')
    # Stream hash avoids retaining the Blender archive in memory.
    with archive.open('rb') as stream:
        archive_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    need(archive_hash == values['BLENDER_SHA256'], 'pinned Blender archive checksum')
    need(run([str(binary), '--version']).splitlines()[0] == 'Blender 4.5.3', 'pinned Blender version')
    codec = (APP/'tools/web_derivatives.sh').read_text()
    pins = dict(re.findall(r'^GT_(CLI|CORE|FUNCTIONS|EXTENSIONS)_VERSION=([^\s#]+)', codec, re.M))
    need(pins == dict.fromkeys(('CLI', 'CORE', 'FUNCTIONS', 'EXTENSIONS'), '4.5.0'), 'exact existing codec closure')
    cli = ['npx', '--yes']
    for name in ('cli', 'core', 'functions', 'extensions'):
        cli += ['--package', '@gltf-transform/'+name+'@4.5.0']
    cli += ['gltf-transform']
    return binary, cli


def refresh_request(args):
    """Author a fresh external request from a REAL clean source commit; never APP-write."""
    source_app = args.source_app.resolve()
    need(source_app.name == '4d' and source_app.parent.name == 'chicago', 'explicit source APP root')
    nested_owner = REPO == source_app.parents[1]/'_t1789_capture_owner'
    need(nested_owner or (not source_app.is_relative_to(REPO) and not APP.is_relative_to(source_app.parents[1])), 'distinct typed refresh source/driver repositories')
    source = run(['git', 'rev-parse', 'HEAD'], app=source_app)
    need(HEX40.fullmatch(args.source) and source == args.source, 'actual immutable refresh source')
    need(run(['git','rev-parse','--show-toplevel'],app=source_app) == str(source_app.parents[1]), 'actual refresh repository root')
    need(run(['git', 'rev-parse', 'HEAD']) == args.definition_sha == source, 'runner-refresh requires actual source and definition at the same immutable commit')
    for app in (APP, source_app):
        status = run(['git', 'status', '--porcelain', '--untracked-files=normal'], app=app)
        if nested_owner and app == source_app:
            status = '\n'.join(line for line in status.splitlines() if line != '?? _t1789_capture_owner/')
        need(not status, 'refresh requires both clean source commits')
    template = (APP/MANIFEST).read_bytes()
    need(HEX64.fullmatch(args.manifest_sha256) and digest(template) == args.manifest_sha256, 'exact reviewed request template')
    doc = json.loads(template)
    need(doc['schema'] == 't1789_clothing_capture_request_v2' and doc['release'] is False
         and doc['install'] is False and doc['native_fit_accepted'] is False and doc['material_admission'] is None, 'known noninstalling request template')
    need([tuple(r[k] for k in ('recipe','variant','assembly','liberty')) for r in doc['families']] == FAMILIES, 'strict settler-only refresh')
    names = [r['file'] for r in doc['inputs']]
    need(0 < len(names) <= 512 and len(set(names)) == len(names), 'bounded unique selected refresh paths')
    for name in names: relative(name)
    # Tree membership comes from this actual committed source, never a digest alone.
    tree = subprocess.check_output(['git','ls-tree','-rz','HEAD','--']+['chicago/4d/'+n for n in names], cwd=source_app.parents[1])
    entries = {}
    for record in tree.split(b'\0'):
        if not record: continue
        meta, name = record.decode().split('\t',1); mode, kind, oid = meta.split()
        need(kind == 'blob' and mode in ('100644','100755'), 'regular committed refresh input')
        entries[name.removeprefix('chicago/4d/')] = dict(file=name.removeprefix('chicago/4d/'), mode=mode, git_blob=oid)
    need(set(entries) == set(names), 'every refresh input must exist in actual source Git tree')
    doc['basis_revision'] = source
    doc['status'] = 'SOURCE_ONLY_LINEN_CAPTURE_REQUEST'
    doc['inputs'] = [entries[n] for n in sorted(entries)]
    doc['scope'] = 'Settler linen only; actual committed source and selected inputs bound by authoring. Capture/native fit remain UNRUN until separately admitted workflow.'
    doc['input_binding_scope'] = str(len(entries))+' selected actual committed input bindings; whole source identity is the exact source Git SHA plus clean checkout and tracked APP snapshots, not a complete consumed-dependency claim.'
    raw = (json.dumps(doc,indent=2)+'\n').encode()
    _, out = validate_request(raw,digest(raw),source,source,args.output,app=source_app)
    need(not out.is_relative_to(REPO), 'fresh refresh output outside driver too')
    canonical = ['generators/blender.pin']+['tools/'+n for n in ('human_teamster_blend.py','human_export.py','human_export.sh','human_skin_canonicalize.py','human_web_texture_inputs.py','web_derivatives.sh','human_contract.py')]
    for name in canonical:
        need(file_facts(APP/name)['git_blob'] == file_facts(source_app/name)['git_blob'], 'refresh cannot change a canonical producer')
    out.mkdir(parents=True)
    (out/'clothing-capture-v2.json').write_bytes(raw)
    (out/'REFRESH.json').write_text(json.dumps(dict(status='REQUEST_AUTHORING_ONLY_REQUIRES_REVIEW',source_sha=source,
        driver_sha=args.definition_sha,definition_ref=args.definition_ref,template_sha256=digest(template),request_sha256=digest(raw),
        source_inputs=len(entries),workflow_run=workflow_lineage(),release=False,install=False,producer_run=False),indent=2)+'\n')
    print(json.dumps(dict(status='REQUEST_AUTHORING_ONLY_REQUIRES_REVIEW',request_sha256=digest(raw),release=False)))


def workflow_lineage():
    # Informational actual environment values only; never serialized into request H.
    return {name:os.environ.get(name) for name in ('GITHUB_REPOSITORY','GITHUB_RUN_ID',
        'GITHUB_RUN_ATTEMPT','GITHUB_JOB','GITHUB_WORKFLOW_REF','GITHUB_WORKFLOW_SHA',
        'GITHUB_SHA','GITHUB_EVENT_NAME')}


def capture_request(args, source_app):
    need(args.request is not None, 'reviewed external refreshed request required')
    request = args.request
    need(request.is_file() and not request.is_symlink(), 'regular external request file')
    request = request.resolve()
    need(not request.is_relative_to(REPO) and not request.is_relative_to(source_app.parents[1]), 'request must be outside source and driver repositories')
    need(request.stat().st_size <= 256*1024, 'bounded external request')
    template = (APP/MANIFEST).read_bytes()
    names = [row['file'] for row in json.loads(template)['inputs']]
    need(len(names) == 245 and len(set(names)) == 245, 'the exact finite245-path template is required')
    return request.read_bytes(), names


def capture(args):
    source_app = args.source_app.resolve()
    need(source_app.name == '4d' and source_app.parent.name == 'chicago', 'explicit source APP root')
    nested_owner = args.preflight_only and REPO == source_app.parents[1]/'_t1789_capture_owner'
    need(nested_owner or (not source_app.is_relative_to(REPO) and not APP.is_relative_to(source_app.parents[1])), 'distinct typed driver and clothing checkouts')
    actual = run(['git', 'rev-parse', 'HEAD'], app=source_app)
    need(run(['git', 'rev-parse', '--show-toplevel'], app=source_app) == str(source_app.parents[1]), 'actual clothing repository root')
    driver_sha = run(['git', 'rev-parse', 'HEAD'])
    need(driver_sha == args.definition_sha == actual, 'runner-refresh source and actual workflow definition must be the same immutable commit')
    manifest_raw, input_names = capture_request(args, source_app)
    doc, out = validate_request(manifest_raw, args.manifest_sha256, args.source, actual, args.output, app=source_app, input_names=input_names)
    need(not out.is_relative_to(REPO), 'output must also be outside driver checkout')
    for app in (APP, source_app):
        status = run(['git', 'status', '--porcelain', '--untracked-files=normal'], app=app)
        if nested_owner and app == source_app:
            status = '\n'.join(line for line in status.splitlines() if line != '?? _t1789_capture_owner/')
        need(not status, 'both source checkouts must be clean')
    canonical = ['generators/blender.pin']+['tools/'+n for n in ('human_teamster_blend.py', 'human_export.py', 'human_export.sh', 'human_skin_canonicalize.py', 'human_web_texture_inputs.py', 'web_derivatives.sh', 'human_contract.py')]
    for name in canonical:
        need(file_facts(APP/name)['git_blob'] == file_facts(source_app/name)['git_blob'], 'canonical owner differs between driver and clothing source: '+name)
    if args.preflight_only:
        print(json.dumps({'status':'EXACT_SOURCE_AND_CANONICAL_BINDINGS_VALIDATED_ONLY', 'source_sha':actual, 'driver_sha':driver_sha, 'release':False}))
        return
    execute_capture(args, doc, out, source_app, actual, driver_sha, canonical)


def write_receipt(out, receipt):
    pending = out/'.CAPTURE.pending'
    with pending.open('x') as stream:
        json.dump(receipt, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(pending, out/'CAPTURE.json')
    descriptor = os.open(out, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def execute_capture(args, doc, out, source_app, actual, driver_sha, canonical):
    need(actual == driver_sha == args.definition_sha == args.source, 'capture source/driver/definition must be the same immutable commit')
    before = driver_before = None
    out.mkdir(parents=True)
    receipt = dict(schema='t1789_canonical_parent_capture_v2', status='INCOMPLETE', source_sha=actual,
                   definition_sha=args.definition_sha, definition_ref=args.definition_ref, driver_sha=driver_sha,
                   request_template_sha256=digest((APP/MANIFEST).read_bytes()),workflow_run=workflow_lineage(),
                   request_origin='external refreshed request committed by reviewed SHA256 input',
                   capture_owner_sha256=file_facts(Path(__file__))['sha256'], canonical_owner_blobs={n:file_facts(APP/n)['git_blob'] for n in canonical},
                   manifest_sha256=args.manifest_sha256, release=False, install=False, material_applied=False,
                   production_eligible=False, native_fit_accepted=False, photo_accepted=False,
                   source_before=None, driver_before=None, parent_hashes=None, phase='PREFLIGHT',
                   inventory_omits=['CAPTURE.json'])
    write_receipt(out, receipt)
    failure = None
    try:
        before = source_snapshot(source_app); driver_before = source_snapshot(APP)
        receipt['source_before'] = before; receipt['driver_before'] = driver_before
        binary, cli = prepare_tools()
        receipt['phase'] = 'PRODUCERS'
        write_receipt(out, receipt)
        for row in doc['families']:
            asset = row['variant']; family = out/asset; family.mkdir()
            master = family/'canonical.blend'; rawdir = family/'raw'; rawdir.mkdir()
            parents = family/'parents/assets/humans'; parents.mkdir(parents=True); (parents/'web').mkdir()
            os.environ['HUMAN_EXPORT_EVIDENCE_DIR'] = str(family/'frame-evidence')
            log = family/'producer.log'
            run([str(binary), '-b', '-noaudio', '--factory-startup', '--python-exit-code', '1', '--python', 'tools/human_teamster_blend.py', '--', '--recipe', row['recipe'], '--variant', asset, '--liberty', row['liberty'], '--output', str(master)], log=log, app=source_app)
            run([str(binary), '-b', '-noaudio', str(master), '--python-exit-code', '1', '--python', 'tools/human_export.py', '--', str(rawdir)], log=log, app=source_app)
            frame = family/'frame-evidence'
            need(frame.is_dir() and {p.name for p in frame.iterdir()} == {asset+'.lod'+str(lod)+suffix for lod in range(4) for suffix in ('.raw.glb', '.frame.json')}, 'complete existing rigid-frame evidence required')
            expected = {asset+'.lod'+str(lod)+'.glb' for lod in range(4)}
            need({p.name for p in rawdir.iterdir()} == expected, 'complete four raw LODs only')
            for lod in range(4):
                name = asset+'.lod'+str(lod)+'.glb'; scratch = family/('codec'+str(lod)); scratch.mkdir()
                run(['python3', 'tools/human_skin_canonicalize.py', str(rawdir/name), str(parents/name), '--diagnostics', str(family/(name+'.skin.json'))], log=log, app=source_app)
                for command in codec_commands(parents/name, parents/'web'/name, scratch, cli):
                    run(command, log=log, app=source_app)
            expected_paths = parent_paths(parents, asset)
            run(['python3', 'tools/human_contract.py', '--glb']+[str(parents/p) for p in expected_paths], log=log, app=source_app)
        receipt['parent_hashes'] = [r for r in inventory(out, omit={'CAPTURE.json'}) if '/parents/' in '/'+r['file']]
        need(len(receipt['parent_hashes']) == 8*len(doc['families']), 'complete bounded parent inventory')
        for row in receipt['parent_hashes']:
            row['metadata'] = glb_metadata(out/row['file'])
        receipt['status'] = 'CANONICAL_PARENT_CAPTURE_ONLY'
    except BaseException as error:
        receipt['error'] = type(error).__name__+': '+str(error)
        failure = error
    finally:
        try:
            receipt['source_after'] = source_snapshot(source_app)
            receipt['driver_after'] = source_snapshot(APP)
            need(before is not None and driver_before is not None and receipt['source_after'] == before and receipt['driver_after'] == driver_before, 'APP bytes changed or initial proof incomplete during capture')
            receipt['files'] = inventory(out, omit={'CAPTURE.json'})
        except BaseException as closing_error:
            receipt['status'] = 'INCOMPLETE_CLOSING_PROOF'
            receipt['closing_error'] = type(closing_error).__name__+': '+str(closing_error)
            failure = failure or closing_error
        receipt['phase'] = 'CLOSED'
        write_receipt(out, receipt)
    if failure:
        raise failure
    print(json.dumps({'status': receipt['status'], 'release': False, 'install': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--preflight-only', action='store_true', help='Validate exact source/input/canonical bindings only; no output or producer')
    modes.add_argument('--refresh-request', action='store_true', help='Write reviewable external request from actual clean committed source; no producer')
    parser.add_argument('--source-app', required=True, type=Path)
    parser.add_argument('--request', type=Path, help='Reviewed external refreshed request for preflight/capture; never an APP file')
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--definition-sha', required=True)
    parser.add_argument('--definition-ref', required=True)
    args = parser.parse_args()
    need(HEX40.fullmatch(args.definition_sha), 'actual immutable workflow definition SHA')
    if args.refresh_request:
        need(args.request is None, 'refresh reads only the immutable APP template, not an external request')
        refresh_request(args)
    else: capture(args)


if __name__ == '__main__':
    main()
