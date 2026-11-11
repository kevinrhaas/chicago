"""An enabled habitat clip must ship even when audition-only candidates do not."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

spec = importlib.util.spec_from_file_location('package_audio', Path(__file__).with_name('package_audio.py'))
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)
with tempfile.TemporaryDirectory(prefix='habitat-audio-package-') as tmp:
    root = Path(tmp)
    audio = root/'input'
    audio.mkdir()
    assets = []
    for aid, kind, enabled in [('river', 'environment', False), ('summer-crickets', 'candidate', True), ('frog', 'candidate', False)]:
        data = aid.encode()
        (audio/f'{aid}.mp3').write_bytes(data)
        assets.append({'id': aid, 'kind': kind, 'runtime_enabled': enabled, 'url': f'{aid}.mp3',
                       'delivery': {'sha256': hashlib.sha256(data).hexdigest()}})
    (audio/'catalog.json').write_text(json.dumps({'assets': assets}))
    package.AUDIO = audio
    standard = package.build(root/'standard', 'https://audio.example.com/')
    packed = json.loads((root/'standard/app-catalog.json').read_text())
    assert {a['id'] for a in packed['assets']} == {'river', 'summer-crickets'}
    assert standard['objects'] == 2
    assert all(a['url'].startswith('https://audio.example.com/media/') for a in packed['assets'])
    expanded = package.build(root/'expanded', include_candidates=True)
    assert expanded['objects'] == 3
    assert (audio/'summer-crickets.mp3').read_bytes() == b'summer-crickets'
print('HABITAT PACKAGE PASS: enabled clips always included, audition-only clips opt-in, immutable URLs and authoring files retained')
