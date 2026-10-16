import hashlib, json, os, pathlib
rec = pathlib.Path('docs/RESEARCH/glessner-v4-recovery')
parts = sorted(rec.glob('part-*'))
json.dump({
    'parts': len(parts),
    'bytes': sum(p.stat().st_size for p in parts),
    'manifest_sha256': hashlib.sha256((rec / 'manifest.json').read_bytes()).hexdigest(),
}, (pathlib.Path(os.environ['RUNNER_TEMP']) / 'old/package.json').open('w'))
print(f"current package: {len(parts)} parts, {sum(p.stat().st_size for p in parts):,} B")
