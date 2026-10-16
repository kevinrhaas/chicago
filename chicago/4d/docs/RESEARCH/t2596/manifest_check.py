import hashlib, json, pathlib
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
m = json.loads(pathlib.Path('assets/manifest.json').read_text())
entry = m['assets']['glessner_house__as_built_1887.glb']
light = entry['web_lods']['light']
assert light['output_sha256'] == sha('assets/web/glessner_house__as_built_1887.light.glb'), 'manifest light hash disagrees with the file'
assert light['master_sha256'] == sha('assets/gltf/glessner_house__as_built_1887.glb'), 'manifest master hash disagrees with the file'
print('manifest record agrees with the bytes on disk')
