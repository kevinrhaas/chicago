#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Optional same-run canonical human delivery, restricted to one owned PR branch.

No network download implementation: GitHub's artifact action transfers the exact
producer artifact ID. This helper verifies the fixed member set before writing
fixed app targets. Only `gate` runs the complete native preflight; only `commit`
can commit/push, after the actual gated tree and remote head are rechecked.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import struct
import subprocess
import time

APP = Path(__file__).resolve().parent.parent
REPO = APP.parent.parent
REPOSITORY = 'kevinrhaas/chicago'
BRANCH = 'steward/t1789-people-photoquality-20261026'
REF = 'refs/heads/' + BRANCH
WORKFLOW = REPOSITORY + '/.github/workflows/chicago-4d-humans.yml@' + REF
LEGACY = '1cbb1817508593562f99ed378b6932368b5699b9'
MALES = ('bardwell_otis_1835', 'dufresne_joseph_1835', 'flynn_martin_1835')
FEMALE = 'flynn_mary_1835_dress_study'
PROOF = 'docs/RESEARCH/human-library-1789/delivery'
BUNDLE = Path('/tmp/human-delivery-bundle')
DOWNLOAD = Path('/tmp/human-delivery-download')
STATE = Path('/tmp/human-delivery-state')
SOURCE_FILES = (
    '../../.github/workflows/chicago-4d-humans.yml', 'generators/blender.pin',
    'tools/human_delivery.py', 'tools/test_human_delivery.py',
    'tools/human_teamster_blend.py', 'tools/human_dress_components.py',
    'tools/human_period_wardrobe.py', 'tools/render_human_assembly_stills.py',
    'tools/human_export.sh', 'tools/human_export.py', 'tools/human_skin_canonicalize.py',
    'tools/human_fixture.mjs', 'tools/human_teamster.mjs',
    'data/humans/recipes/worker_1835.json', 'data/humans/recipes/adult_dress_1835.json',
    'assets/authored/humans/makehuman_hm08/SOURCE.json',
    'assets/authored/humans/makehuman_hm08/SOURCE-female.json',
)


def need(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO, text=True).strip()


def validate_context(c):
    need(c['event'] == 'workflow_dispatch' and c['repository'] == REPOSITORY,
         'delivery requires a manual run in the canonical repository')
    need(c['ref'] == REF and c['workflow_ref'] == WORKFLOW, 'not the exact owned workflow/branch')
    need(re.fullmatch(r'[0-9a-f]{40}', c['source']) and c['source'] != LEGACY,
         'invalid source or read-only legacy reproduction')
    need(c['definition'] == c['source'], 'source must equal actual trusted definition SHA')
    need(c['deliver'] is True and c['seated'] is False, 'delivery is opt-in and unseated only')
    need(c['dress'] != c['teamsters'], 'exactly one fixed family per delivery')
    need(c['source_ref'] in ('', c['source']), 'delivery forbids a separate source ref')
    need(all(re.fullmatch(r'[1-9][0-9]*', c[k]) for k in ('run_id', 'attempt')),
         'invalid current run identity')
    return 'dress' if c['dress'] else 'teamsters'


def context():
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    inputs = event['inputs']
    need(event['repository']['full_name'] == REPOSITORY and
         event['repository'].get('fork') is False, 'fork or event repository mismatch')
    c = dict(event=os.environ['GITHUB_EVENT_NAME'], repository=os.environ['GITHUB_REPOSITORY'],
             ref=os.environ['GITHUB_REF'], workflow_ref=os.environ['DEFINITION_REF'],
             source=os.environ['GITHUB_SHA'], definition=os.environ['DEFINITION_SHA'],
             run_id=os.environ['GITHUB_RUN_ID'], attempt=os.environ['GITHUB_RUN_ATTEMPT'],
             deliver=inputs.get('deliver_generated_assets') == 'true',
             seated=inputs.get('build_seated_driver_study', 'false') == 'true',
             dress=inputs.get('build_dress_study', 'false') == 'true',
             teamsters=inputs.get('build_teamsters', 'false') == 'true',
             source_ref=inputs.get('source_ref', ''))
    c['family'] = validate_context(c)
    need(git('rev-parse', 'HEAD') == c['source'], 'checkout is not the exact run source')
    return c


def assets(family):
    need(family in ('dress', 'teamsters'), 'unknown family')
    return (FEMALE,) if family == 'dress' else MALES


def master(asset):
    group = 'dress' if asset == FEMALE else 'teamsters'
    return f'assets/authored/humans/{group}/{asset}/canonical.blend'


def spec(family):
    """Pairs (producer file, fixed app destination); no manifest-directed paths."""
    root = Path('/tmp/dress-study' if family == 'dress' else '/tmp/teamster-studies')
    rows = [(APP / master(a), master(a)) for a in assets(family)]
    for a in assets(family):
        rows += [(APP / f'assets/humans/{web}{a}.lod{lod}.glb',
                  f'assets/humans/{web}{a}.lod{lod}.glb')
                 for web in ('', 'web/') for lod in range(4)]
    proof = f'{PROOF}/{family}'
    rows += [(root / mode / 'inspection.json', f'{proof}/{mode}-inspection.json')
             for mode in ('source', 'web')]
    for a in assets(family):
        for web in ('', 'web-'):
            for lod in range(4):
                name = f'{web}lod{lod}.validation.json' if family == 'dress' else f'{web}{a}.lod{lod}.glb.validation.json'
                rows.append((root / name, f'{proof}/validators/{name}'))
    if family == 'dress':
        rows.append((root / 'source-binding.json', f'{proof}/source-binding.json'))
    else:
        stills = Path('/tmp/teamster-blender-stills')
        names = ['manifest.json']
        names += [a + suffix for a in MALES for suffix in ('-assembly-threequarter.png', '-receipt.json')]
        rows += [(stills / n, f'{proof}/blender-stills/{n}') for n in names]
    return rows


def regular_under(root, relative):
    p = PurePosixPath(relative)
    need(relative == p.as_posix() and not p.is_absolute() and
         all(x not in ('', '.', '..') for x in p.parts) and '\\' not in relative,
         'unsafe relative member path')
    need(not root.is_symlink(), 'symlink root')
    current = root
    for part in p.parts:
        current /= part
        need(not current.is_symlink(), 'symlink in file path')
    need(current.resolve().is_relative_to(root.resolve()), 'path escaped fixed root')
    need(stat.S_ISREG(current.stat().st_mode) and current.stat().st_nlink == 1,
         'member is not an independent regular file')
    return current


def source_binding(c):
    bound = {}
    for name in SOURCE_FILES:
        p = (APP / name).resolve()
        rel = p.relative_to(REPO).as_posix()
        expected = subprocess.check_output(['git', 'show', f"{c['source']}:{rel}"], cwd=REPO)
        need(hashlib.sha256(expected).hexdigest() == digest(p), 'source file changed: ' + rel)
        bound[rel] = digest(p)
    return bound


def glb_container(path, asset):
    with path.open('rb') as stream:
        header = stream.read(20)
        need(len(header) == 20, 'short GLB')
        magic, version, total, length, kind = struct.unpack('<5I', header)
        need(magic == 0x46546C67 and version == 2 and total == path.stat().st_size and
             kind == 0x4E4F534A and 0 < length <= min(total - 20, 16 * 1024 * 1024), 'invalid GLB container')
        data = json.loads(stream.read(length))
    need(all('uri' not in row for key in ('buffers', 'images') for row in data.get(key, [])),
         'external or data URI is forbidden in delivered GLBs')
    human = data['scenes'][0]['extras']['chicago4d_human']
    need(human['asset_id'] == asset and human['grade'] == 'reconstructed', 'GLB identity/grade mismatch')


def verify_reports(c, root):
    family = c['family']; proof = root / PROOF / family
    for mode in ('source', 'web'):
        j = json.loads((proof / f'{mode}-inspection.json').read_text())
        need(j['mechanical_passed'] is True and j['failures'] == [], 'native inspection failed/incomplete')
        expected = {f'assets/humans/{"web/" if mode == "web" else ""}{a}.lod{l}.glb'
                    for a in assets(family) for l in range(4)}
        pairs = {(row['file'], row['viewport_name']) for row in j['runs']}
        need(pairs == {(p, vp) for p in expected for vp in ('desktop', 'mobile')} and
             len(j['runs']) == len(pairs), 'inspection does not cover the exact family/LODs/viewports')
        for row in j['runs']:
            need(row['sha256'] == digest(root / row['file']) and row['checks'] and
                 all(v is True for v in row['checks'].values()) and
                 row['page_errors'] == [] and row['failed_requests'] == [], 'inspection hash/check mismatch')
    for path in (proof / 'validators').iterdir():
        j = json.loads(path.read_text())
        need(j['issues']['numErrors'] == 0 and not j['issues'].get('truncated'), 'container validator failure')
    if family == 'dress':
        j = json.loads((proof / 'source-binding.json').read_text())
        need(j['source_sha'] == c['source'] and j['workflow_definition_sha'] == c['definition'] and
             str(j['run_id']) == c['run_id'] and str(j['run_attempt']) == c['attempt'], 'dress source binding mismatch')
    else:
        j = json.loads((proof / 'blender-stills/manifest.json').read_text())
        need(j['status'] == 'actual_three_native_Blender_stills_completed' and
             j['source_sha'] == c['source'] and j['definition_sha'] == c['definition'] and
             str(j['run_id']) == c['run_id'] and str(j['run_attempt']) == c['attempt'] and
             j['fixed_assets'] == list(MALES) and re.fullmatch(r'4\.5\.3(?: LTS)?', j['blender_version']) and
             len(j['renders']) == 3, 'incomplete or wrong-source native Blender stills')
        for a, row in zip(MALES, j['renders']):
            receipt = json.loads((proof / f'blender-stills/{a}-receipt.json').read_text())
            need(receipt == row and row['asset_id'] == a and row['source_protection_verified'] is True and
                 row['status'] == 'actual_native_render_completed' and
                 row['master_sha256_before'] == row['master_sha256_after'] == digest(root / master(a)) and
                 row['source_body_rig_geometry_state_before'] == row['source_body_rig_geometry_state_after'],
                 'native Blender master/body/rig protection mismatch')
            image = proof / f'blender-stills/{a}-assembly-threequarter.png'
            need(row['PNG']['sha256'] == digest(image) and image.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n',
                 'native still PNG mismatch')


def bundle(c):
    need(not BUNDLE.exists(), 'fresh bundle directory required')
    binding = source_binding(c)
    BUNDLE.mkdir()
    rows = []
    for source, target in spec(c['family']):
        need(not source.is_symlink() and source.is_file(), 'missing/symlink producer output')
        # Parent directories are trusted fixed producer paths, still refuse symlinks.
        regular_under(APP if source.is_relative_to(APP) else Path('/tmp'),
                      source.relative_to(APP if source.is_relative_to(APP) else Path('/tmp')).as_posix())
        dest = BUNDLE / target; dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        rows.append(dict(path=target, bytes=dest.stat().st_size, sha256=digest(dest)))
    verify_reports(c, BUNDLE)
    j = dict(format='canonical_human_delivery_v1', repository=REPOSITORY, branch=BRANCH,
             source_sha=c['source'], definition_sha=c['definition'], source_tree=git('rev-parse', 'HEAD^{tree}'),
             run_id=c['run_id'], run_attempt=c['attempt'], family=c['family'], source_files=binding,
             photographic_accepted=False, production_eligibility_changed=False, files=rows)
    dump(BUNDLE / 'delivery-manifest.json', j)
    with Path(os.environ['GITHUB_OUTPUT']).open('a') as stream:
        stream.write('manifest_sha256=' + digest(BUNDLE / 'delivery-manifest.json') + '\n')


def verify_bundle(c):
    mf = regular_under(DOWNLOAD, 'delivery-manifest.json')
    need(digest(mf) == os.environ['EXPECTED_MANIFEST_SHA256'], 'producer manifest digest mismatch')
    j = json.loads(mf.read_text())
    expected = {target for _, target in spec(c['family'])}
    actual = set()
    for path in DOWNLOAD.rglob('*'):
        need(not path.is_symlink(), 'symlink in artifact')
        if not path.is_dir():
            actual.add(path.relative_to(DOWNLOAD).as_posix())
    need(actual == expected | {'delivery-manifest.json'}, 'unexpected/missing artifact members')
    need(j['format'] == 'canonical_human_delivery_v1' and j['repository'] == REPOSITORY and
         j['branch'] == BRANCH and j['source_sha'] == c['source'] and j['definition_sha'] == c['definition'] and
         j['source_tree'] == git('rev-parse', 'HEAD^{tree}') and j['family'] == c['family'] and
         j['run_id'] == c['run_id'] and j['run_attempt'] == c['attempt'] and
         j['source_files'] == source_binding(c) and j['photographic_accepted'] is False and
         j['production_eligibility_changed'] is False, 'bundle source/run/family mismatch')
    need(len(j['files']) == len(expected) and {v['path'] for v in j['files']} == expected,
         'manifest rows do not equal fixed full family')
    for row in j['files']:
        p = regular_under(DOWNLOAD, row['path'])
        need(p.stat().st_size == row['bytes'] and digest(p) == row['sha256'], 'member SHA/size mismatch')
    for a in assets(c['family']):
        for web in ('', 'web/'):
            for lod in range(4):
                glb_container(DOWNLOAD / f'assets/humans/{web}{a}.lod{lod}.glb', a)
    verify_reports(c, DOWNLOAD)
    return j


def remote_source(c):
    urls = ('https://github.com/kevinrhaas/chicago', 'https://github.com/kevinrhaas/chicago.git')
    need(git('remote', 'get-url', 'origin') in urls and
         git('remote', 'get-url', '--push', '--all', 'origin') in urls, 'unexpected fetch/push remote')
    result = git('ls-remote', '--exit-code', 'origin', REF).split()
    need(result == [c['source'], REF], 'feature branch advanced; refusing delivery')


def require_female_delivery(c):
    """Male write mode starts only after the complete prior female delivery.

    The later male definition commit differs because the female files were
    committed. Its authoring source must remain byte-identical to the reviewed
    female recipe/helpers, and the actual installed female members must match.
    """
    p = APP / 'data/humans/canonical-deliveries/dress.json'
    need(p.is_file() and not p.is_symlink(), 'finish female delivery before male delivery')
    j = json.loads(p.read_text())
    need(j['family'] == 'dress' and j['repository'] == REPOSITORY and j['branch'] == BRANCH and
         re.fullmatch(r'[0-9a-f]{40}', j['source_sha']) and j['source_sha'] == j['definition_sha'] and
         j['source_files'] == source_binding(c) and j['photographic_accepted'] is False,
         'male source is not equivalent to the previously delivered female source')
    subprocess.run(['git', 'merge-base', '--is-ancestor', j['source_sha'], c['source']], cwd=REPO, check=True)
    changed = set(git('diff', '--name-only', j['source_sha'], c['source']).splitlines())
    need(changed <= allowed({'family': 'dress'}),
         'authoring/shared input changed after female generation; only fixed female delivery paths may differ')
    expected = {target for _, target in spec('dress')}
    need(len(j['files']) == len(expected) and {row['path'] for row in j['files']} == expected,
         'prior female delivery member set incomplete')
    for row in j['files']:
        path = regular_under(APP, row['path'])
        need(path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], 'prior female delivery bytes changed')


def artifact(c):
    artifact_id = os.environ['DELIVERY_ARTIFACT_ID']
    need(re.fullmatch(r'[1-9][0-9]*', artifact_id), 'invalid producer artifact ID')
    j = json.loads(subprocess.check_output(['gh', 'api', f'repos/{REPOSITORY}/actions/artifacts/{artifact_id}'], text=True))
    w = j['workflow_run']
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    repository_id = event['repository']['id']
    need(str(j['id']) == artifact_id and not j['expired'] and
         j['name'] == f"human-delivery-{c['family']}-{c['run_id']}-{c['attempt']}" and
         str(w['id']) == c['run_id'] and w['head_sha'] == c['source'] and w['head_branch'] == BRANCH and
         w['repository_id'] == repository_id and w['head_repository_id'] == repository_id and
         re.fullmatch(r'sha256:[0-9a-f]{64}', j['digest']), 'not the exact current-run producer artifact')
    need(os.environ['FIXTURE_RESULT'] == 'success' and os.environ['PRODUCER_RESULT'] == 'success',
         'native prerequisite/generation job did not succeed')
    STATE.mkdir(exist_ok=True)
    dump(STATE / 'artifact.json', {k: j[k] for k in ('id', 'name', 'digest', 'size_in_bytes', 'workflow_run')})
    remote_source(c)


def install(c):
    j = verify_bundle(c); remote_source(c)
    need(not git('status', '--porcelain', '--untracked-files=all'), 'delivery checkout must be clean')
    need(shutil.disk_usage(APP).free >= sum(row['bytes'] for row in j['files']) + 2 * 1024**3,
         'insufficient delivery/native-gate scratch capacity')
    for row in j['files']:
        dest = APP / row['path']
        # Existing file or nearest existing parent must remain inside the checkout.
        parent = dest
        while not parent.exists():
            need(not parent.is_symlink(), 'symlink target'); parent = parent.parent
        need(parent.resolve().is_relative_to(APP) and not parent.is_symlink(), 'target escapes app')
        for p in (dest, *dest.parents):
            if p == APP:
                break
            need(not p.is_symlink(), 'symlink target ancestor')
        if dest.exists():
            need(stat.S_ISREG(dest.stat().st_mode) and dest.stat().st_nlink == 1, 'unsafe existing target')
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DOWNLOAD / row['path'], dest)
    dump(STATE / 'installed-manifest.json', j)


def metadata(c):
    j = verify_bundle(c); art = json.loads((STATE / 'artifact.json').read_text())
    measure = json.loads((APP / 'data/humans/fixture.measure.json').read_text())
    files = {row['file']: row for row in measure['files']}
    actual = {p.relative_to(APP).as_posix() for d in ('assets/humans', 'assets/humans/web')
              for p in (APP / d).glob('*.glb')}
    need(set(files) == actual and len(files) == len(measure['files']), 'ALL-asset measurement census mismatch')
    for name, row in files.items():
        verdicts = row.get('verdicts')
        need(isinstance(verdicts, list) and verdicts and
             all(isinstance(v, dict) and isinstance(v.get('check'), str) and v['check'] and
                 'got' in v and v.get('ok') is True for v in verdicts),
             'unqualified/invalid native measurement verdict list')
        need(row['sha256'] == digest(APP / name), 'unqualified/stale combined measurement')
    receipt = dict(j, artifact_id=art['id'], artifact_zip_sha256=art['digest'].split(':')[1],
                   delivery_manifest_sha256=os.environ['EXPECTED_MANIFEST_SHA256'],
                   mechanical_scope='Same-source canonical generation and ALL-asset browser/LOD qualification; '
                   'published scene/photo/occupied acceptance remain open')
    dump(APP / f"data/humans/canonical-deliveries/{c['family']}.json", receipt)
    lines = [f"\n\n### Actual optional {c['family']} canonical delivery — run{c['run_id']} attempt{c['attempt']}\n",
             f"Source `{c['source']}`, definition `{c['definition']}`, artifact{art['id']}, "
             f"official ZIP SHA256 `{receipt['artifact_zip_sha256']}`, manifestSHA256 `{receipt['delivery_manifest_sha256']}`. "
             'CC0-1.0 graphical derivatives retain all existing MakeHuman body/hair/skin source notices above; '
             'original garment/bonnet/closure/hat geometry and generated material values are CC0-1.0. '
             'Generator code remains GPL-3.0-or-later. Dress finishing and rounded felt dimensions/colors are '
             'reconstructed, bounded by the existing cleared period sources; no new likeness or historical outfit '
             'is asserted. Mechanical pipeline qualification does not establish photographic/production acceptance.\n',
             '\n|Path under assets/|License|Bytes|SHA256|\n|---|---|---:|---|\n']
    for row in j['files']:
        if row['path'].startswith('assets/'):
            lines.append(f"|{row['path'][7:]}|CC0-1.0, original notices retained|{row['bytes']}|{row['sha256']}|\n")
    with (APP / 'assets/LICENSES.md').open('a') as stream:
        stream.write(''.join(lines))
    if c['family'] == 'teamsters':
        old = json.loads((APP / 'data/humans/bardwell_otis_1835.measure.json').read_text())
        old.update(canonical_source_sha=c['source'], canonical_run_id=int(c['run_id']),
                   canonical_artifact_id=art['id'], canonical_artifact_zip_sha256=receipt['artifact_zip_sha256'],
                   mechanical_qualified=True, photographic_accepted=False,
                   scope=receipt['mechanical_scope'], assets=[])
        proof = APP / PROOF / c['family']
        for mode in ('source', 'web'):
            report = json.loads((proof / f'{mode}-inspection.json').read_text())
            for row in report['runs']:
                if row['viewport_name'] != 'desktop' or not Path(row['file']).name.startswith(MALES[0] + '.'):
                    continue
                m = files[row['file']]
                old['assets'].append(dict(file=row['file'], lod=m['lod'], sha256=m['sha256'],
                    bytes=m['bytes'], triangles=row['triangles'], skinned_meshes=row['skinned_meshes'],
                    bone_count=row['bone_count'], standing_frame=row['standing_frame'],
                    footwear_min_y_m=row['footwear_min_y_m'], draw_material_slots=m['draw_calls'],
                    decoded_images=[{'material': x['name'], 'textures': x['textures']} for x in row['materials']]))
        need(len(old['assets']) == 8, 'actual Bardwell eight-file cost receipt incomplete')
        dump(APP / 'data/humans/bardwell_otis_1835.measure.json', old)
        p = APP / 'data/humans/instances/1835/hi_rc_bardwell_otis_1835.json'
        instance = json.loads(p.read_text())
        need(instance['appearance']['asset_id'] == MALES[0] and instance['behaviour']['state'] == 'standing' and
             instance['animation']['clip'] == 'idle', 'existing standing Otis selection changed')
        instance['provenance']['basis'] = (
            f"Reconstructed standing depiction of existing reconstructed resident Otis Bardwell; canonical "
            f"source{c['source']}, run{c['run_id']}, artifact{art['id']}. Existing invented Wolf Point Tavern-yard "
            'stand, placement and identity are preserved. Name, age band and teamster role are model records, '
            'not documentary identity, likeness, tavern employment, wagon ownership or an observed action. '
            'The current workwear/rounded felt hat is reconstructed within the existing cleared source bounds. '
            'Mechanical source/export qualification does not establish photographic period fidelity, continuous '
            'animated fit, occupied interfaces or scene performance. Those remain open.')
        dump(p, instance)
        change = json.loads((APP / 'changelog.d/T-1789.json').read_text())
        change['title'] = 'Refine the standing resident and reusable wardrobe'
        change['items'] = ['Otis Bardwell’s standing model uses the rebuilt workwear and rounded hat. '
                           'Three additional resident-reference models form part of the reusable library; '
                           'they have no new town placements. All appearances remain reconstructions.']
        dump(APP / 'changelog.d/T-1789.json', change)


def allowed(c):
    names = {target for _, target in spec(c['family'])}
    names |= {'assets/LICENSES.md', 'data/humans/fixture.measure.json',
              f"data/humans/canonical-deliveries/{c['family']}.json"}
    if c['family'] == 'teamsters':
        names |= {'data/humans/bardwell_otis_1835.measure.json',
                  'data/humans/instances/1835/hi_rc_bardwell_otis_1835.json', 'changelog.d/T-1789.json'}
    return {'chicago/4d/' + name for name in names}


def sealed_tree(c):
    source_binding(c)
    names = set(git('diff', '--cached', '--name-only', c['source']).splitlines())
    need(names and names <= allowed(c), 'unexpected/empty staged delivery paths')
    need(not git('diff', '--name-only') and not git('ls-files', '--others', '--exclude-standard'),
         'unstaged/untracked source changes after delivery')
    need(not git('ls-files', '-u'), 'unmerged delivery index')
    # No symlink modes are acceptable, even if a later step replaced an installed file.
    for name in names:
        need(git('ls-files', '-s', '--', name).startswith('100644 '), 'unexpected staged file mode')
    for row in verify_bundle(c)['files']:
        need(digest(APP / row['path']) == row['sha256'], 'installed output changed since verified bundle')
    return git('write-tree')


def gate(c):
    remote_source(c)
    subprocess.run(['git', 'add', '--', *sorted(allowed(c))], cwd=REPO, check=True)
    before = sealed_tree(c)
    env = dict(os.environ, C4D_GATE_REQUIRE_READERS='1', C4D_GATE_REQUIRE_BASE='1',
               CHECK_JOBS='4', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    env.pop('GIT_NO_LAZY_FETCH', None)
    start = time.monotonic()
    with (STATE / 'native-preflight.log').open('w') as stream:
        result = subprocess.run(['bash', 'tools/preflight.sh'], cwd=APP, env=env,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=1800)
    need(result.returncode == 0, 'complete required-reader native preflight failed; no commit')
    need(sealed_tree(c) == before, 'staged/source tree changed during native preflight')
    remote_source(c)
    dump(STATE / 'GATED-TREE.json', dict(source=c['source'], tree=before,
         manifest_sha256=os.environ['EXPECTED_MANIFEST_SHA256'], artifact_id=os.environ['DELIVERY_ARTIFACT_ID'],
         run_id=c['run_id'], attempt=c['attempt'], family=c['family'], returncode=result.returncode,
         seconds=time.monotonic()-start, required_readers=True, required_base=True,
         origin_dev=git('rev-parse', 'origin/dev'), preflight_log_sha256=digest(STATE / 'native-preflight.log')))


def commit(c):
    seal = json.loads((STATE / 'GATED-TREE.json').read_text())
    need(seal['returncode'] == 0 and seal['required_readers'] is True and seal['required_base'] is True and
         seal['source'] == c['source'] and seal['run_id'] == c['run_id'] and seal['attempt'] == c['attempt'] and
         seal['family'] == c['family'] and seal['tree'] == sealed_tree(c) and
         seal['manifest_sha256'] == os.environ['EXPECTED_MANIFEST_SHA256'] and
         seal['artifact_id'] == os.environ['DELIVERY_ARTIFACT_ID'] and
         seal['preflight_log_sha256'] == digest(STATE / 'native-preflight.log'), 'gated-tree/source receipt mismatch')
    remote_source(c)
    git('config', 'user.name', 'github-actions[bot]')
    git('config', 'user.email', 'github-actions[bot]@users.noreply.github.com')
    git('commit', '-m', f"feat: deliver canonical {c['family']} human assets (T-1789)",
        '-m', f"Same-run generated models from {c['source']}; run {c['run_id']} attempt {c['attempt']}. "
        f"Complete required-reader preflight sealed tree {seal['tree']}. Photographic/production acceptance remains open.")
    head = git('rev-parse', 'HEAD')
    need(git('rev-parse', 'HEAD^') == c['source'] and git('rev-parse', 'HEAD^{tree}') == seal['tree'],
         'actual commit parent/tree does not match the gated delivery')
    subprocess.run(['git', 'diff', '--check', 'HEAD^', 'HEAD'], cwd=REPO, check=True)
    base = git('merge-base', 'origin/dev', 'HEAD')
    subprocess.run(['node', 'tools/check-changelog-entry.mjs', base, head], cwd=APP, check=True)
    subprocess.run(['node', 'tools/resolve_id_collisions.mjs', '--base', 'origin/dev', '--check'],
                   cwd=APP, check=True)
    need(not git('status', '--porcelain', '--untracked-files=all'), 'actual new HEAD is not clean')
    # Immediately before a NORMAL non-force push. A race after this check is still
    # refused by Git's fast-forward rule; there is no force/update-ref/API bypass.
    remote_source(c)
    git('push', 'origin', 'HEAD:' + REF)
    need(git('ls-remote', '--exit-code', 'origin', REF).split() == [head, REF], 'pushed remote head mismatch')
    dump(STATE / 'ACTUAL-PUSH.json', dict(source=c['source'], HEAD=head, TREE=seal['tree'],
         branch=BRANCH, ordinary_PR_CI='PENDING: GITHUB_TOKEN push does not trigger normal PR checks; '
         'root must verify this exact gated tree and use normal authenticated same-tree followup',
         auto_ready=False, auto_merge=False, photographic_accepted=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('guard', 'bundle', 'artifact', 'install', 'metadata', 'gate', 'commit'))
    command = parser.parse_args().command
    c = context()
    if c['family'] == 'teamsters':
        require_female_delivery(c)
    if command != 'guard':
        globals()[command](c)


if __name__ == '__main__':
    main()
