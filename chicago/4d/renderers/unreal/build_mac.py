#!/usr/bin/env python3
"""Build a fresh local Mac preview from committed glTF; requires licensed UE + Xcode."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True, help='Unreal Engine 5.8.2 installation')
    parser.add_argument('--project-dir', type=Path, required=True, help='NEW generated project directory')
    parser.add_argument('--archive-dir', type=Path, required=True, help='NEW packaged output directory')
    args = parser.parse_args()
    template = Path(__file__).resolve().parent
    source = template.parent.parent
    project = args.project_dir.resolve()
    archive = args.archive_dir.resolve()
    engine = args.engine.resolve()
    if project.exists() or archive.exists():
        parser.error('Use new project and archive directories; existing work is never overwritten.')
    editor = engine / 'Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor'
    build = engine / 'Engine/Build/BatchFiles/Mac/Build.sh'
    uat = engine / 'Engine/Build/BatchFiles/RunUAT.sh'
    for required in (editor, build, uat, source/'data/scenes/1835.json'):
        if not required.exists():
            parser.error(f'Missing prerequisite: {required}')
    version = json.loads((engine/'Engine/Build/Build.version').read_text())
    if (version['MajorVersion'], version['MinorVersion'], version['PatchVersion']) != (5, 8, 2):
        parser.error('This adapter was validated with Unreal 5.8.2; qualify other versions separately.')
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain', '--', '.'], text=True).strip()
    if dirty:
        parser.error('Commit the source tree first so the build has an unambiguous revision.')
    project.mkdir(parents=True)
    for name in ('Source', 'Config', 'Scripts'):
        shutil.copytree(template/name, project/name)
    shutil.copy2(template/'Chicago4D.uproject', project/'Chicago4D.uproject')
    (project/'Content').mkdir()
    game_config = project/'Config/DefaultGame.ini'
    game_config.write_text(game_config.read_text().replace('0.1.0-dev.253f02657', f'0.1.0-dev.{commit[:9]}'))
    environment = dict(os.environ, CHICAGO_SOURCE=str(source), CHICAGO_PROJECT=str(project), CHICAGO_COMMIT=commit)
    uproject = project/'Chicago4D.uproject'

    def run(label, command):
        log = project/'Scripts'/f'{label}.log'
        print(f'{label}: {log}', flush=True)
        with log.open('w') as output:
            subprocess.run([str(x) for x in command], env=environment, stdout=output, stderr=subprocess.STDOUT, check=True)

    run('editor-build', [build, 'Chicago4DEditor', 'Mac', 'Development', f'-project={uproject}', '-waitmutex'])
    run('import', [editor, uproject, '-run=pythonscript', f'-script={project}/Scripts/import_scene.py', '-unattended', '-nullrhi', '-nosplash'])
    report = json.loads((project/'Scripts/import_report.json').read_text())
    if report['errors'] or not report.get('level'):
        raise RuntimeError('Import did not complete; no app will be packaged.')
    run('verify', [editor, uproject, '-run=pythonscript', f'-script={project}/Scripts/verify_scene.py', '-unattended', '-nullrhi', '-nosplash'])
    if not (project/'Scripts/verification.json').exists():
        raise RuntimeError('Scene verification did not finish.')
    run('package', [uat, 'BuildCookRun', f'-project={uproject}', '-noP4', '-platform=Mac', '-architecture=arm64',
                    '-clientconfig=Development', '-build', '-cook', '-stage', '-pak', '-package', '-archive',
                    f'-archivedirectory={archive}', '-unattended', '-utf8output'])
    apps = list(archive.rglob('Chicago4D.app'))
    if len(apps) != 1:
        raise RuntimeError(f'Expected one packaged app, found {len(apps)}')
    binary = apps[0]/'Contents/MacOS/Chicago4D'
    receipt = {'source_commit': commit, 'engine': version, 'architecture': 'arm64',
               'configuration': 'Development', 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
               'import': report, 'play_test': 'Not performed by build script; launch and verify walking separately.'}
    (archive/'build-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    shutil.copy2(template/'README.md', archive/'README.md')
    print(f'Packaged app: {apps[0]}', flush=True)


if __name__ == '__main__':
    main()
