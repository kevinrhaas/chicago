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
    assert sum(a['scene_placement']['mode'] in ['habitat-insects', 'distant-bird'] for a in enabled) == 3
    assert sum(a['scene_placement']['mode'] == 'moving-transport' for a in enabled) == 2
print('HABITAT REGENERATION PASS: existing preparation preserves all placement metadata and reproduces the same33 assets/40 delivery hashes')
