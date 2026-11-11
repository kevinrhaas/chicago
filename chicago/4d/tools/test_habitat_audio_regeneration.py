"""Rebuild deliveries in a fresh directory; never write through source symlinks.
This integration proof uses ffmpeg/ffprobe and is not proposed as a fast gate step.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('C4D_SOURCE_ROOT', HERE))
spec = importlib.util.spec_from_file_location('prepare_audio', SOURCE/'tools/prepare_audio.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)
expected = json.loads((HERE/'renderers/web/audio/catalog.json').read_text())
with tempfile.TemporaryDirectory(prefix='habitat-regeneration-') as tmp:
    root = Path(tmp)
    authoring = root/'assets/audio'
    authoring.mkdir(parents=True)
    (root/'data').symlink_to(SOURCE/'data', target_is_directory=True)
    (authoring/'originals').symlink_to(SOURCE/'assets/audio/originals', target_is_directory=True)
    (authoring/'evidence').symlink_to(SOURCE/'assets/audio/evidence', target_is_directory=True)
    shutil.copyfile(HERE/'assets/audio/intake.json', authoring/'intake.json')
    output = root/'renderers/web/audio'
    output.mkdir(parents=True)
    # --library-only never writes music. Effects have fresh, non-symlink outputs.
    for a in expected['assets']:
        if a['kind'] == 'music':
            for key in ['opus', 'aac']:
                p = output/a[key]
                p.parent.mkdir(parents=True, exist_ok=True)
                p.symlink_to(SOURCE/'renderers/web/audio'/a[key])
    prepare.ROOT = root
    prepare.ORIGINALS = authoring/'originals'
    prepare.OUT = output
    sys.argv = ['prepare_audio.py', '--library-only']
    prepare.main()
    actual = json.loads((output/'catalog.json').read_text())
    assert actual == expected, 'regeneration changed a delivery, provenance field or placement declaration'
    assert json.loads((authoring/'catalog.json').read_text()) == expected
    enabled = [a for a in actual['assets'] if a.get('runtime_enabled') is True]
    assert sum(a.get('scene_placement', {}).get('mode') in ['habitat-insects', 'distant-bird'] for a in enabled) == 3
    assert sum(a.get('scene_placement', {}).get('mode') == 'moving-transport' for a in enabled) == 2
    approved_river = next(a for a in actual['assets'] if a['id'] == 'river')
    assert approved_river['kind'] == 'environment' and approved_river['runtime_enabled'] is True
    assert approved_river['delivery'] == {'bytes': 352940, 'sha256': '6831b7ad102ec023194c4040776c5245b6cb47451d652a94a07dc742e28362af'}
    held_river = next(a for a in actual['assets'] if a['id'] == 'river-held')
    assert held_river['runtime_enabled'] is False
    assert held_river['delivery'] == {'bytes': 352940, 'sha256': 'a63798768beaff4eba54e79293c89b81e9940d87d8742b45b0ac93130610bd5a'}
    asset_count = len(actual['assets'])
    delivery_count = sum(2 if a['kind'] == 'music' else 1 for a in actual['assets'])
print(f'HABITAT REGENERATION PASS: placement metadata preserved; {asset_count} assets/{delivery_count} delivery hashes reproduced')
