"""Refresh only the three legacy comparisons with the ordinary UV bake.

Run with the pinned Blender: -b -P <this file>. The current detailed house has
physical material UVs and was built separately with --no-bake. The legacy
versions use emit's ordinary smart unwrap; preserve that distinction.
"""
from pathlib import Path
import datetime as dt
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'generators'))
import emit
import mesh_inputs
from build import inputs_hash,resolve_phase
from common.versions import load_versions,read_manifest,write_manifest,asset_key

manifest=read_manifest();manifest['inputs_scheme']=mesh_inputs.SCHEME
for version in load_versions():
    if version['id']!='glessner_house' or version['label'] not in ('pre-v4','v2','v3'):continue
    record=version['record'];phase=resolve_phase(record,dt.date(1904,7,1))
    key=asset_key(record['id'],version['label'],phase['id'])
    made=emit.emit_structure(record,phase,record['archetype'],ROOT/'assets/gltf'/key,bake=True,ao=False)
    manifest['assets'][key]={
        'kind':'generated','structure_id':record['id'],'version_label':version['label'],
        'phase_id':phase['id'],'archetype':record['archetype'],
        'inputs_sha256':inputs_hash(record,phase,record['archetype']),
        'bytes':made.path.stat().st_size,'baked_ao':False}
    print(f'built {key}: {made.tris} triangles, ordinary UV unwrap')
write_manifest(manifest)
