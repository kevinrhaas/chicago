# SPDX-License-Identifier: GPL-3.0-or-later
"""Fetch three unchanged canonical masters from a successful same-repository build.

Only the explicitly requested completed human workflow is a source. The source and
consumer commits are recorded separately; this does not regenerate or adopt assets.
Authentication is inherited by gh; credentials never enter arguments or receipts.
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
import subprocess
import tempfile
import zipfile

ASSETS = ('bardwell_otis_1835', 'dufresne_joseph_1835', 'flynn_martin_1835')
LIMIT = 1024 ** 3
WORKFLOW = '.github/workflows/chicago-4d-humans.yml'


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def select_artifact(repo, run_id, run, jobs, artifacts):
    if (run.get('id') != int(run_id) or run.get('path') != WORKFLOW or
        run.get('event') != 'workflow_dispatch' or run.get('status') != 'completed' or
        run.get('conclusion') != 'success' or
        run.get('head_repository', {}).get('full_name', '').lower() != repo.lower() or
        not re.fullmatch(r'[0-9a-f]{40}', run.get('head_sha', ''))):
        raise ValueError('source must be the completed successful same-repository human workflow')
    for name in ('humans', 'teamster-studies'):
        matches = [job for job in jobs if job.get('name') == name]
        if len(matches) != 1 or any(matches[0].get(k) != v for k, v in
                                  (('status', 'completed'), ('conclusion', 'success'))):
            raise ValueError(f'source prerequisite {name} must have completed successfully')
    matches = [a for a in artifacts if a.get('name') == 'resident-teamster-studies-'+run['head_sha']]
    if len(matches) != 1:
        raise ValueError('source must contain exactly one canonical teamster artifact')
    artifact = matches[0]
    if (artifact.get('expired') is not False or not isinstance(artifact.get('id'), int) or
        not 0 < artifact.get('size_in_bytes', 0) <= LIMIT or
        not re.fullmatch(r'sha256:[0-9a-f]{64}', artifact.get('digest') or '')):
        raise ValueError('source artifact must be unexpired, bounded and SHA256-bound')
    return artifact


def verify_archive(path, digest):
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', digest) or sha256(path) != digest[7:]:
        raise ValueError('artifact bytes do not match the server SHA256 digest')


def selected_members(archive):
    selected, names = {}, set()
    for entry in archive.infolist():
        name = entry.filename
        parts = name.rstrip('/').split('/')
        if (not name or PurePosixPath(name).is_absolute() or '\\' in name or
            any(p in ('', '.', '..') for p in parts) or name in names or
            stat.S_ISLNK(entry.external_attr >> 16)):
            raise ValueError('artifact contains an unsafe or duplicate ZIP path')
        names.add(name)
        for asset in ASSETS:
            suffix = f'assets/authored/humans/teamsters/{asset}/canonical.blend'
            if name == suffix or name.endswith('/'+suffix):
                if asset in selected or entry.is_dir() or not 0 < entry.file_size <= LIMIT:
                    raise ValueError('canonical master is duplicated, empty or oversized')
                selected[asset] = entry
    if set(selected) != set(ASSETS) or sum(i.file_size for i in selected.values()) > LIMIT:
        raise ValueError('artifact must contain exactly the three bounded canonical masters')
    return selected


def extract_masters(archive_path, output):
    if output.exists():
        raise ValueError('output-dir must be fresh; preserving existing evidence')
    with zipfile.ZipFile(archive_path) as archive:
        members = selected_members(archive)
        output.mkdir(parents=True)
        records = []
        for asset in ASSETS:
            dest = output / asset / 'canonical.blend'
            dest.parent.mkdir()
            with archive.open(members[asset]) as source, dest.open('xb') as target:
                shutil.copyfileobj(source, target)
            records.append({'asset_id': asset, 'archive_path': members[asset].filename,
                            'path': str(dest.relative_to(output)), 'bytes': dest.stat().st_size,
                            'sha256': sha256(dest)})
    return records


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', path], text=True, timeout=60))


def pages(path, key):
    result = []
    for page in range(1, 11):
        batch = api(f'{path}?per_page=100&page={page}')[key]
        result.extend(batch)
        if len(batch) < 100:
            return result
    raise ValueError('source metadata exceeded the bounded pagination limit')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    repo = os.environ.get('GITHUB_REPOSITORY', '')
    consumer = os.environ.get('GITHUB_SHA', '')
    if not re.fullmatch(r'[1-9][0-9]{0,19}', args.run):
        parser.error('--run must be a positive numeric GitHub run ID')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo) or not re.fullmatch(r'[0-9a-f]{40}', consumer):
        parser.error('GITHUB_REPOSITORY and immutable GITHUB_SHA are required')
    output = args.output_dir.absolute()
    if output.exists():
        parser.error('output-dir must be fresh')
    prefix = f'repos/{repo}/actions/runs/{args.run}'
    run = api(prefix)
    artifact = select_artifact(repo, args.run, run, pages(prefix+'/jobs', 'jobs'),
                               pages(prefix+'/artifacts', 'artifacts'))
    with tempfile.TemporaryDirectory(prefix='human-library-intake-') as scratch:
        archive = Path(scratch)/'source.zip'
        with archive.open('xb') as target:
            subprocess.run(['gh', 'api', f'repos/{repo}/actions/artifacts/{artifact["id"]}/zip'],
                           stdout=target, check=True, timeout=180)
        if archive.stat().st_size > LIMIT:
            raise ValueError('download exceeded the archive byte limit')
        verify_archive(archive, artifact['digest'])
        masters = extract_masters(archive, output)
    binding = {'schema': 'chicago4d_human_library_stills_source_v1', 'repository': repo,
               'source_run_id': int(args.run), 'source_run_url': run['html_url'],
               'source_head_sha': run['head_sha'], 'source_workflow': run['path'],
               'consumer_head_sha': consumer,
               'artifact': {key: artifact[key] for key in ('id', 'name', 'digest', 'size_in_bytes')},
               'masters': masters, 'scope': 'render-only source snapshot; no runtime asset adoption'}
    (output/'source-binding.json').write_text(json.dumps(binding, indent=2)+'\n')
    print(json.dumps({'source_run_id': int(args.run), 'source_head_sha': run['head_sha'],
                      'consumer_head_sha': consumer, 'artifact_id': artifact['id'], 'masters': len(masters)}))


if __name__ == '__main__':
    main()
