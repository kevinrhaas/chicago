#!/usr/bin/env python3
"""Build an upload-ready audio bundle without uploading or changing app hosting.

python tools/package_audio.py --output /tmp/chicago-audio-release
Use --public-base https://audio.example.com/ after choosing a real asset host.
The generated app-catalog.json is the small app-side catalogue for that host.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / 'renderers/web/audio'


def build(output, public_base=None, include_candidates=False):
    if public_base:
        url = urlparse(public_base)
        if url.scheme != 'https' or not url.netloc or url.query or url.fragment or url.username or url.password:
            raise ValueError('public base must be an HTTPS URL without credentials, query or fragment')
        public_base = public_base.rstrip('/') + '/'
    if output.exists() and any(output.iterdir()):
        raise ValueError('output must be absent or empty; use a new release directory')
    (output/'media').mkdir(parents=True, exist_ok=True)
    catalog = json.loads((AUDIO/'catalog.json').read_text())
    catalog['assets'] = [a for a in catalog['assets'] if include_candidates or a['kind'] != 'candidate' or a.get('runtime_enabled') is True]
    manifest = {}
    for asset in catalog['assets']:
        for field in ('opus', 'aac') if asset['kind'] == 'music' else ('url',):
            source = (AUDIO/asset[field]).resolve()
            if not source.is_relative_to(AUDIO.resolve()):
                raise ValueError('source media must be inside the local audio directory')
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            expected = asset['delivery'][field]['sha256'] if asset['kind'] == 'music' else asset['delivery']['sha256']
            if digest != expected:
                raise ValueError(f'{source.name}: catalogue hash does not match')
            key = 'media/' + digest + source.suffix
            target = output/key
            if not target.exists():
                shutil.copyfile(source, target)
            manifest[key] = {'sha256': digest, 'bytes': source.stat().st_size,
                'content_type': {'.ogg':'audio/ogg', '.m4a':'audio/mp4', '.mp3':'audio/mpeg'}[source.suffix],
                'cache_control': 'public, max-age=31536000, immutable'}
            asset[field] = (public_base or '') + key
    (output/'app-catalog.json').write_text(json.dumps(catalog, indent=2)+'\n')
    (output/'upload-manifest.json').write_text(json.dumps({'objects':manifest,'media_bytes':sum(x['bytes'] for x in manifest.values()),
        'public_base':public_base,'includes_review_candidates':include_candidates},indent=2)+'\n')
    (output/'cors.json').write_text(json.dumps([{'AllowedOrigins':['https://chicago.polecat.live'],
        'AllowedMethods':['GET','HEAD'],'AllowedHeaders':['Range'],
        'ExposeHeaders':['Accept-Ranges','Content-Length','Content-Range','ETag'],'MaxAgeSeconds':3600}],indent=2)+'\n')
    (output/'README.txt').write_text('Upload media/ using the MIME and cache headers in upload-manifest.json.\n'
        'Configure CORS for the actual production and development origins. Both currently use chicago.polecat.live.\n'
        'Use a production custom domain; Cloudflare r2.dev is a development endpoint.\n'
        'Verify GET, HEAD, Range (206), CORS, checksums and browser playback before switching the app catalogue.\n'
        'No originals, account credentials or upload operations are included.\n'
        'Do not remove local delivery files until the hosted catalogue passes release verification.\n')
    return {'assets':len(catalog['assets']),'objects':len(manifest),'media_bytes':sum(x['bytes'] for x in manifest.values())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--public-base')
    parser.add_argument('--include-candidates', action='store_true')
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.public_base, args.include_candidates)))
