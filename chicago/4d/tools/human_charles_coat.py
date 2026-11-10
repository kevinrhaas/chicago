#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Own the existing Charles near-coat derivative without restoring unknown bodies.

Bare/--check writes/checks only the reproducible registration receipt. Expensive
--reproduce is explicit and used by the canonical export's transactional finish.
The immutable parent recipe remains byte-exact to the reviewed material study.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

APP = Path(__file__).resolve().parents[1]
RECIPE = APP/'data/humans/materials/charles-coat-woven-v1.json'
ADMISSION = APP/'data/humans/materials/charles-coat-woven-v1.admission.json'
RECEIPT = APP/'data/humans/materials/charles-coat-woven-v1.derivation.json'
ASSET = 'nelson_charles_1904_coachman'
RECIPE_SHA256 = '2b604e409564a0340c497bd158307a22620aad3efaa542aecff55a2e0d8dc4d3'
IMPLEMENTATION = ('tools/human_charles_coat.py', 'tools/human_charles_coat.mjs',
                  'tools/human_charles_coat_semantics.mjs', 'tools/human_charles_coat_web.sh',
                  'tools/verify_human_charles_coat.py', 'tools/human_export.sh')
RUNTIME = ('renderers/web/js/fabric.js', 'renderers/web/js/human-looks.js')


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(require_implementation=True):
    recipe, admission = json.loads(RECIPE.read_bytes()), json.loads(ADMISSION.read_bytes())
    need(recipe['asset_id'] == admission['asset_id'] == ASSET, 'Charles-only registration')
    need(sha(RECIPE.read_bytes()) == admission['recipe_sha256'] == RECIPE_SHA256, 'reviewed authoring recipe changed; never retarget without reproduction/qualification')
    need(admission['parent_revision'] == recipe['parent_revision'] == 'fc5a52b6cab3eed78e2db5864aa811dff5df2795', 'exact canonical parent reference')
    paths = {f'assets/humans/{web}{ASSET}.lod{lod}.glb' for web in ('', 'web/') for lod in range(4)}
    near = {p for p in paths if '.lod0.' in p or '.lod1.' in p}
    need({r['file'] for r in recipe['parents']} == paths and len(recipe['parents']) == 8, 'eight explicit parent bindings')
    need({r['file'] for r in admission['outputs']} == near and len(admission['outputs']) == 4, 'only four near outputs')
    need(admission['volatile_path_allowlist'] == [{'pointer': '/scenes/0/extras/chicago4d_human/master', 'type': 'absolute_path_string', 'reason': 'Historical authoring file location; no runtime consumer. All adjacent provenance, source IDs/hashes/versions/license/style and rig booleans remain protected.'}], 'no broadened metadata exclusion')
    if require_implementation:
        need(admission.get('implementation_sha256') == {f: sha((APP/f).read_bytes()) for f in IMPLEMENTATION}, 'implementation differs from actual reproduction admission; reproduce externally and review the proof before rebinding')
        need(admission.get('runtime_sha256') == {f: sha((APP/f).read_bytes()) for f in RUNTIME}, 'coupled cloth/recolor runtime differs from the actual reviewed study')
    return recipe, admission


def parse(raw):
    need(len(raw) >= 28 and struct.unpack_from('<III', raw) == (0x46546c67, 2, len(raw)), 'complete GLB2')
    n, kind = struct.unpack_from('<II', raw, 12)
    need(kind == 0x4e4f534a and n % 4 == 0, 'JSON chunk')
    doc = json.loads(raw[20:20+n])
    size, kind = struct.unpack_from('<II', raw, 20+n)
    binary = raw[28+n:]
    need(kind == 0x004e4942 and size == len(binary), 'single complete embedded BIN')
    need(not any(b.get('uri') for b in doc.get('buffers', [])) and not any(i.get('uri') for i in doc.get('images', [])), 'embedded canonical human family only')
    return doc, binary


def parent_semantics(raw):
    """Conservative semantic equality: all bindings+BIN exact, one path ignored.

    This deliberately rejects even harmless binary repacking. Equal full BIN and
    equal bindings are stronger than equality of every expanded PN/UV/JW/morph,
    rig/clip/image stream. Generator/version/hash/proof objects are NOT ignored.
    """
    doc, binary = parse(raw)
    need(len(doc['scenes']) == 1, 'one canonical human scene')
    human = doc['scenes'][0]['extras']['chicago4d_human']
    need(human['asset_id'] == ASSET, 'actual canonical identity')
    location = human['master']
    need(type(location) is str and location.startswith('/') and '\0' not in location, 'only the enumerated absolute authoring path may normalize')
    human['master'] = '<absolute-authoring-master-path>'
    return dict(json_sha256=sha(json.dumps(doc, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()),
                binary_sha256=sha(binary), binary_bytes=len(binary))


def compatible(canonical, fresh):
    expected, actual = parent_semantics(canonical), parent_semantics(fresh)
    need(expected == actual, 'fresh parent changes protected geometry/UV/skin/morph/rig/clips/material/provenance/version/hash or unknown metadata; refusing before active writes')
    return dict(fresh_sha256=sha(fresh), canonical_sha256=sha(canonical), exact_full_BIN_and_all_nonvolatile_JSON=True,
                normalized_only='/scenes/0/extras/chicago4d_human/master', fingerprint=expected)


def parent_bytes(row, recipe, parent_root=None):
    """Explicit cache/active-parent first, then existing Git objects; never fetch."""
    for candidate in ([Path(parent_root)/row['file']] if parent_root else []) + [APP/row['file']]:
        if candidate.is_file():
            raw = candidate.read_bytes()
            if sha(raw) == row['sha256']:
                need(len(raw) == row['bytes'], 'canonical parent size')
                need(hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest() == row['gitBlob'], 'canonical Git blob identity')
                return raw
    root = APP.parents[1]
    env = dict(os.environ, GIT_NO_LAZY_FETCH='1')
    try:
        tree = subprocess.check_output(['git', 'ls-tree', recipe['parent_revision'], '--', 'chicago/4d/'+row['file']], cwd=root, env=env).decode().split()
        need(len(tree) >= 3 and tree[2] == row['gitBlob'], 'canonical parent tree binding')
        raw = subprocess.check_output(['git', 'cat-file', 'blob', row['gitBlob']], cwd=root, env=env)
    except (subprocess.CalledProcessError, ValueError) as error:
        raise ValueError('immutable parent unavailable offline/shallow; provide an explicit verified --parent-root or fetch reviewed history separately; no active file written') from error
    need(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'exact immutable parent SHA and size')
    return raw


def dependencies(explicit):
    if explicit:
        return Path(explicit).resolve()
    cli = shutil.which('gltf-transform')
    need(cli, 'run inside the owning pinned npx closure, or provide --dependencies')
    # node_modules/@gltf-transform/cli/bin/cli.js, resolved from .bin symlink.
    root = Path(cli).resolve().parents[3]
    need((root/'@gltf-transform/core/package.json').is_file() and (root/'mikktspace/package.json').is_file(), 'pinned CLI and Mikk must share one dependency closure')
    return root


def require_parent_tree(recipe, root=None):
    """A shallow/offline checkout must fail before any active or output write."""
    root = APP.parents[1] if root is None else Path(root)
    env = dict(os.environ, GIT_NO_LAZY_FETCH='1')
    for row in recipe['parents']:
        result = subprocess.run(['git', 'ls-tree', recipe['parent_revision'], '--', 'chicago/4d/'+row['file']],
                                cwd=root, env=env, capture_output=True, text=True)
        fields = result.stdout.split()
        need(result.returncode == 0 and len(fields) >= 3 and fields[2] == row['gitBlob'],
             'reviewed immutable tree unavailable in shallow/offline checkout; fetch the declared history separately before reproduction; no active file written')


def reproduce(out, dependency_root, parent_root=None):
    # Candidate reproduction may measure changed code; it never installs it.
    # Active export and cheap gate registration require the admitted code hashes.
    recipe, admission = load(require_implementation=False)
    out = Path(out).resolve()
    need(not out.exists() and not out.is_relative_to(APP), 'fresh external reproduction output only')
    require_parent_tree(recipe)
    # Resolve every immutable input before creating any output or active write.
    parents = [(row, parent_bytes(row, recipe, parent_root)) for row in recipe['parents']]
    with tempfile.TemporaryDirectory(prefix='charles-coat-reproduce-') as temp:
        temp = Path(temp)
        for row, raw in parents:
            path = temp/'parents'/row['file']; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        subprocess.run(['node', str(APP/'tools/human_charles_coat.mjs'), str(RECIPE), str(temp/'parents'), str(temp/'master'), str(dependency_root)], check=True)
        subprocess.run(['bash', str(APP/'tools/human_charles_coat_web.sh'), str(RECIPE), str(temp/'parents'), str(temp/'master'), str(temp/'web'), str(dependency_root)], check=True)
        results = []
        for row in admission['outputs']:
            raw = (temp/('web' if '/web/' in row['file'] else 'master')/Path(row['file']).name).read_bytes()
            need(sha(raw) == row['sha256'] and len(raw) == row['bytes'], 'actual regeneration differs from the validated source/WEB child; STOP for new qualification, never retarget expected hashes')
            results.append((row['file'], raw))
        out.mkdir()
        for file, raw in results:
            target = out/file; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        proof = dict(schema='charles_coat_actual_reproduction_v1', recipe_sha256=sha(RECIPE.read_bytes()),
                     parent_revision=recipe['parent_revision'], implementation_sha256={f: sha((APP/f).read_bytes()) for f in IMPLEMENTATION},
                     runtime_sha256={f: sha((APP/f).read_bytes()) for f in RUNTIME},
                     inputs=[dict(file=row['file'], sha256=sha(raw), gitBlob=row['gitBlob']) for row, raw in parents],
                     outputs=[dict(file=file, sha256=sha(raw), bytes=len(raw)) for file, raw in results],
                     strict_semantics=True, install=False, full_release_or_photo_accepted=False)
        (out/'REPRODUCTION.json').write_text(json.dumps(proof, indent=2)+'\n')
    return results


def active_state(target, parents, outputs):
    """Never replace an unknown/currently improved active body with old assets."""
    existing = [(row, target/row['file'].removeprefix('assets/humans/')) for row, raw in parents]
    if not any(path.exists() for row, path in existing):
        return 'fresh'
    need(all(path.is_file() for row, path in existing), 'partial active family refused')
    wanted = {row['file']: row for row in outputs}
    for row, path in existing:
        raw = path.read_bytes()
        if row['file'] in wanted and sha(raw) == wanted[row['file']]['sha256']:
            continue
        need(sha(raw) == row['sha256'], 'unknown active/far body refused; do not restore a frozen parent over a changed asset')
    return 'bound'


def install_files(writes):
    """All inputs were proved first; roll back the whole quartet on an IO fault."""
    backups = {path: path.read_bytes() if path.exists() else None for path, raw in writes}
    try:
        for path, raw in writes:
            path.parent.mkdir(parents=True, exist_ok=True)
            pending = path.with_name(path.name+'.charles-pending')
            need(not pending.exists(), 'stale pending file refused')
            pending.write_bytes(raw); os.replace(pending, path)
    except BaseException:
        for path, original in backups.items():
            if original is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(original)
            path.with_name(path.name+'.charles-pending').unlink(missing_ok=True)
        raise


def finish_export(exported, target, dependency_root, parent_root=None):
    recipe, admission = load(); exported, target = Path(exported).resolve(), Path(target).resolve()
    expected = {row['file'].removeprefix('assets/humans/') for row in recipe['parents']}
    need({p.relative_to(exported).as_posix() for p in exported.rglob('*.glb')} == expected, 'only the complete eight-file Charles canonical family may finish')
    parents = [(row, parent_bytes(row, recipe, parent_root)) for row in recipe['parents']]
    state = active_state(target, parents, admission['outputs'])
    proofs = []
    for row, canonical in parents:
        fresh = (exported/row['file'].removeprefix('assets/humans/')).read_bytes()
        proofs.append(dict(file=row['file'], parent_ref=recipe['parent_revision'], gitBlob=row['gitBlob'], **compatible(canonical, fresh)))
    # All eight fresh/protected parents are now compatible. Canonicalize only the
    # enumerated ephemeral path by using the bound baseline; retain source SHA.
    with tempfile.TemporaryDirectory(prefix='charles-coat-finish-') as temp:
        results = reproduce(Path(temp)/'result', dependency_root, parent_root)
        writes = [(target/file.removeprefix('assets/humans/'), raw) for file, raw in results]
        if state == 'fresh':
            changed = {file for file, raw in results}
            writes += [(target/row['file'].removeprefix('assets/humans/'), raw) for row, raw in parents if row['file'] not in changed]
        install_files(writes)
    return dict(changed_near_files=4, far_active_files_written=0 if state == 'bound' else 4,
                fresh_compatibility=proofs, full_release_or_photo_accepted=False)


def receipt(parent_root=None):
    recipe, admission = load(); rows = []
    for parent in recipe['parents']:
        expected = next((r for r in admission['outputs'] if r['file'] == parent['file']), parent)
        raw = (APP/parent['file']).read_bytes()
        need(sha(raw) == expected['sha256'] and len(raw) == expected['bytes'], 'active derivative/far baseline differs: '+parent['file'])
        rows.append(dict(file=parent['file'], sha256=sha(raw), bytes=len(raw), changed=parent['lod'] < 2,
                         canonical_parent_sha256=parent['sha256'], canonical_git_blob=parent['gitBlob']))
        if parent['lod'] < 2 and '/web/' not in parent['file']:
            # Independent raw component/metadata verifier is lightweight and
            # needs no NPM/Blender. Missing immutable history fails closed here.
            from verify_human_charles_coat import verify
            verify(parent_bytes(parent, recipe, parent_root), raw, RECIPE.read_bytes(), parent['lod'])
    return dict(schema='charles_near_coat_registration_v1', recipe_sha256=sha(RECIPE.read_bytes()),
                admission_sha256=sha(ADMISSION.read_bytes()), parent_revision=recipe['parent_revision'],
                implementation_sha256={f: sha((APP/f).read_bytes()) for f in IMPLEMENTATION}, files=rows,
                runtime_sha256={f: sha((APP/f).read_bytes()) for f in RUNTIME},
                strict_selected_published_release=False, full_APP_gate=False, photographic_or_fit_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--reproduce', type=Path)
    mode.add_argument('--finish-export', type=Path)
    parser.add_argument('--target', type=Path)
    parser.add_argument('--dependencies', type=Path)
    parser.add_argument('--parent-root', type=Path)
    args = parser.parse_args()
    if args.reproduce:
        reproduce(args.reproduce, dependencies(args.dependencies), args.parent_root)
    elif args.finish_export:
        need(args.target is not None, '--finish-export requires --target')
        print(json.dumps(finish_export(args.finish_export, args.target, dependencies(args.dependencies), args.parent_root)))
    else:
        data = json.dumps(receipt(args.parent_root), indent=2)+'\n'
        if args.check:
            need(RECEIPT.read_text() == data, 'derivation registration stale; run tools/human_charles_coat.py after actual reproduction/admission')
        else:
            RECEIPT.write_text(data)
        print(json.dumps(dict(registered=8, changed=4, checked=args.check, full_release_or_photo_accepted=False)))


if __name__ == '__main__':
    main()
