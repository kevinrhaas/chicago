#!/usr/bin/env python3
"""Check uploaded audio objects without changing the bucket or app.

python tools/verify_audio_host.py --manifest /path/upload-manifest.json
Checks full hashes, browser-origin CORS, MIME types and HTTP byte ranges.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request
from urllib.parse import urlparse


def verify(manifest, public_base=None, origin='https://chicago.polecat.live'):
    base = (public_base or manifest.get('public_base') or '').rstrip('/') + '/'
    parsed = urlparse(base)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('a public HTTPS media base is required')
    errors, rows = [], []
    headers = {'User-Agent':'Mozilla/5.0 Chicago4D-AudioVerifier/1.0', 'Origin':origin}
    for key, entry in manifest['objects'].items():
        if not key.startswith('media/') or '..' in key or '?' in key or '#' in key:
            raise ValueError('invalid object key')
        try:
            with urllib.request.urlopen(urllib.request.Request(base+key, headers=headers), timeout=30) as r:
                data = r.read(entry['bytes']+1)
                cors = r.headers.get('Access-Control-Allow-Origin')
                mime = r.headers.get('Content-Type','').split(';')[0]
                cache = r.headers.get('Cache-Control','')
                if r.status != 200: raise ValueError(f'GET status {r.status}')
            if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
                raise ValueError('uploaded bytes do not match the prepared file')
            if cors not in (origin,'*'): raise ValueError(f'CORS did not allow {origin}')
            # R2's dashboard labels .m4a uploads audio/x-m4a. Browsers support
            # that established alias; API uploads use canonical audio/mp4.
            accepted = {entry['content_type']}
            if entry['content_type'] == 'audio/mp4': accepted.add('audio/x-m4a')
            if mime not in accepted: raise ValueError(f'MIME {mime}, expected {entry["content_type"]}')
            with urllib.request.urlopen(urllib.request.Request(base+key, headers={**headers,'Range':'bytes=0-63'}), timeout=30) as r:
                if r.status != 206 or r.headers.get('Content-Range') != f'bytes 0-63/{entry["bytes"]}':
                    raise ValueError('byte-range response is not the expected HTTP 206')
                if r.read(65) != data[:64]: raise ValueError('byte-range contents differ')
            rows.append({'key':key,'bytes':len(data),'content_type':mime,'cache_control':cache})
            print('PASS',key,flush=True)
        except (urllib.error.URLError, ValueError, TimeoutError) as e:
            errors.append({'key':key,'error':str(e)})
            print('FAIL',key,str(e),flush=True)
            # A missing first object usually means upload is not complete. Do
            # not repeat forty identical requests or trigger needless retries.
            if not rows: break
    return {'public_base':base,'origin':origin,'verified':rows,'errors':errors,
        'complete':not errors and len(rows)==len(manifest['objects'])}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--public-base')
    parser.add_argument('--origin',default='https://chicago.polecat.live')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    result=verify(json.loads(args.manifest.read_text()),args.public_base,args.origin)
    if args.report: args.report.write_text(json.dumps(result,indent=2)+'\n')
    print('AUDIO HOST PASS' if result['complete'] else 'AUDIO HOST NOT VERIFIED')
    raise SystemExit(0 if result['complete'] else 1)
