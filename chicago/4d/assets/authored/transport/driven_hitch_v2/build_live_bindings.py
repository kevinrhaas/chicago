#!/usr/bin/env python3
"""Source-bound live guide references and explicit per-LOD palm receipts."""
import json,numpy as np
from pathlib import Path
from build_hitch_prototype import HERE,HORSE,read,accessor,ray_hit,sha
d,b=read(HORSE.read_bytes());pr=d['meshes'][1]['primitives'][0]
P=accessor(d,b,pr['attributes']['POSITION']).astype(float);F=accessor(d,b,pr['indices']).reshape(-1,3).astype(int)
guides={}
for sign,side in [(1,'left'),(-1,'right')]:
    for kind,zs in [('trace',[.6,.45,.3,.15,0,-.15,-.3,-.45,-.6,-.75]),('cheek',[1.30,1.20,1.10])]:
        rows=[]
        for z in zs:
            y=1.24-(.75-z)/1.5*.14 if kind=='trace' else 1.43+(1.4-z)/.35*.05
            direction=np.array([sign,0.,0.]);point,face,bary=ray_hit(P,F,np.array([0.,y,z]),direction)
            rows.append({'face':int(face),'indices':F[face].tolist(),'barycentric':bary.tolist(),'rest_outward':direction.tolist(),'normal_offset_m':.025 if kind=='trace'else .012,'rest_surface_m':point.tolist()})
        guides[kind+'_'+side]=rows
source_bind=json.loads((HERE/'collar-surface-bindings.json').read_text())
bands={r['name']:{'first_vertex':r['first_vertex'],'segments':48}for r in source_bind['ranges']}
palmFile=Path(globals()['PALM_SOURCE_OVERRIDE'])
palm=json.loads(palmFile.read_text())
palms=[]
for row in palm['rows']:
    palms.append({'scene':'1835','asset_id':'bardwell_otis_1835','web':row['web'],'lod':row['lod'],'actual_asset_sha256':row['sha256'],'actual_asset_path':'assets/humans/'+('web/'if row['web']else'')+Path(row['file']).name,
        'points_m':{v['side']:v['endpoint_vehicle_local_m']for v in row['actual_palm_endpoints']},
        'actual_triangle_indices':{v['side']:v['triangle_vertex_indices']for v in row['actual_palm_endpoints']},'clip':'sit_drive','clip_time_s':.5,'closed_finger_grip_verified':False})
out={'schema':'current26_live_draft_hitch_bindings_v2','horse_source_sha256':sha(HORSE.read_bytes()),'source_body_material_name':d['materials'][1]['name'],'source_body_vertex_count':len(P),'joint_names':[n['name']for n in d['nodes'][:26]],'bands':bands,'surface_guides':guides,
    'wood_yoke_radius_m':.025,'team_half_spacing_m':.65,'singletree_halfwidth_m':.45,'evener_relative_y_m':-.04,'evener_relative_z_m':-.105,'trace_contact_scope':'New surface-bound guides and collar rims, not inherited certified tack sockets. Full global-body/trace collision and native/world render remain unrun.',
    'palm_records':palms,'palm_source_receipt':{'evidence_name':palmFile.name,'sha256':sha(palmFile.read_bytes())},
    'vehicle_bindings':{'wagon_w01':{'pole_node':'vehicle_tongue','tip_node':'vehicle_hitch_team','reuse_existing_pivot':True,'horse_center_z_root_m':3.4987,'front_axle_node':'vehicle_steer_front','singletree_root_z_m':1.9,'singletree_root_y_m':.72},
        'studebaker_brougham_1893':{'pole_node':'vehicle_team_pole','tip_node':'vehicle_hitch_team','reuse_existing_pivot':False,'new_pivot_root_m':[0,.553,1.15],'horse_center_z_root_m':3.08,'front_axle_node':'vehicle_steer_front','singletree_root_z_m':1.9,'singletree_root_y_m':.72,'derivative_scope':'Independent driven clone only: source rear beam centre becomes explicit front-axle steering/lift pivot; original parked model and all geometry/material bytes remain unchanged.'}},
    'all_native_harness_render_world_qualification':'UNRUN'}
(HERE/'live-hitch-bindings-v2.json').write_text(json.dumps(out,indent=2)+'\n');print(HERE/'live-hitch-bindings-v2.json')
