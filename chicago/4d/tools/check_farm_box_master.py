#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only freshness and actual emitted mechanical contract for T-2793.

Continuous front-wheel/body separation is a conservative geometric proof.
Other interfaces are bounded geometry checks, not a strength/harness/physics
certification. The actual reviewed model remains a labeled reconstruction.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/transport/farm_box'))
from adapt_old_cart import make
from licensed_source import Source, SOURCE_SHA256
from mechanics import Master, front_swept_clearance, intersections, wagon_code_regions


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    recipe_path = ROOT/'data/transport/studies/farm-box-master.json'
    recipe = json.loads(recipe_path.read_bytes())
    authored = ROOT/'assets/authored/transport/farm_box_master_v1'
    master_path = authored/'derived/farm-box-source.glb'
    raw,sidecar = make(recipe)
    if master_path.read_bytes()!=raw:
        raise ValueError('Authored master is stale: regenerate the actual producer')
    sidecar['glb_sha256'] = hashlib.sha256(raw).hexdigest()
    if json.loads((authored/'derived/farm-box-source.json').read_bytes())!=sidecar:
        raise ValueError('Authored engine-neutral sidecar is stale')
    source = Source(authored/'old-cart-original.glb')
    master = Master(master_path)
    if master.g['asset']['extras']!=source.gltf['asset']['extras']:
        raise ValueError('Original embedded author/license/source credit changed')
    if master.g['materials']!=source.gltf['materials'] or master.g.get('samplers')!=source.gltf.get('samplers'):
        raise ValueError('Canonical original materials/samplers changed')
    required={'vehicle_root':None,'vehicle_body':'vehicle_root','vehicle_steer_front':'vehicle_root',
              'vehicle_running_gear_rear':'vehicle_root','vehicle_tongue':'vehicle_steer_front',
              'vehicle_kingbolt':'vehicle_steer_front','vehicle_reach':'vehicle_body'}
    for end,parent in [('front','vehicle_steer_front'),('rear','vehicle_running_gear_rear')]:
        for side in ['left','right']:
            required[f'vehicle_wheel_{end}_{side}']=parent
    for name,parent in required.items():
        i = master.names[name]
        actual = master.g['nodes'][master.parents[i]]['name'] if i in master.parents else None
        if actual!=parent:
            raise ValueError('Detached or incorrect articulation: '+name)
    root_position=master.translation('vehicle_root')
    if not np.array_equal(root_position,[0,0,0]):
        raise ValueError('Hidden master origin offset')
    if not np.array_equal(master.translation('vehicle_body'),[0,0,0]):
        raise ValueError('Body offset invalidates the canonical metre/clearance frame')
    body_points=master.positions('CartBody_CartBase_0')
    if not np.allclose(np.ptp(body_points[:,[2,0]],axis=0),recipe['body_m'][:2],atol=1e-6):
        raise ValueError('Actual metre body envelope changed')
    ground=[]
    for end,source_nodes in [('front',[12,10]),('rear',[14,16])]:
        radius=recipe['wheel_radius_m'][end]
        for side,source_node in zip(['left','right'],source_nodes):
            frame=f'vehicle_wheel_{end}_{side}'
            centre=master.translation(frame)
            expected=[(1 if side=='left'else-1)*recipe['wheel_center_track_m']/2,radius,recipe['axle_stations_z_m'][end]]
            if not np.allclose(centre,expected,atol=1e-7):
                raise ValueError('Incorrect emitted axle/track/axis frame: '+frame)
            mesh_name=next(r['name']for r in sidecar['parts']if r['original_node']==source_node)
            tyre=master.positions(mesh_name)[np.unique(source.components(source_node)[0]['indices'])]
            radial_max=float(np.hypot(tyre[:,1],tyre[:,2]).max())
            # The artist rim is not a mathematical circle: retain and disclose
            # its measured <=3mm small-scale irregularity, rather than claim
            # zero penetration in an unsupported suspension simulation.
            neutral_gap=float(centre[1]+tyre[:,1].min())
            worst_rolling_lower_bound=float(centre[1]-radial_max)
            if abs(neutral_gap)>.00001 or abs(worst_rolling_lower_bound)>.003:
                raise ValueError('Actual tyre/ground envelope exceeds declared mesh tolerance: '+frame)
            ground.append({'frame':frame,'neutral_ground_gap_m':neutral_gap,'all_roll_ground_lower_bound_m':worst_rolling_lower_bound,
                           'scope':'Original artist rim irregularity retained, <=3mm; not perfect-circle or suspension certification'})
    for name,mesh in master.meshes.items():
        mesh_node=master.names[name]
        parent_name=master.g['nodes'][master.parents[mesh_node]]['name']
        if not np.array_equal(master.translation(name),master.translation(parent_name)):
            raise ValueError('Hidden mesh-child offset: '+name)
        p = mesh['primitives'][0]
        positions = master.positions(name)
        indices = master.accessor(p['indices']).reshape(-1,3)
        if len(np.unique(indices))!=len(positions):
            raise ValueError('Phantom unused POSITION bounds: '+name)
        accessor = master.g['accessors'][p['attributes']['POSITION']]
        if not np.array_equal(positions.min(axis=0),accessor['min']) or not np.array_equal(positions.max(axis=0),accessor['max']):
            raise ValueError('Incorrect actual POSITION bounds: '+name)
        triangles = positions[indices]
        if np.any(np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)<1e-10):
            raise ValueError('Degenerate actual triangle: '+name)
        for semantic in ['NORMAL','TANGENT']:
            values = master.accessor(p['attributes'][semantic])
            if not np.all(np.isfinite(values)) or np.max(np.abs(np.linalg.norm(values[:,:3],axis=1)-1))>2e-6:
                raise ValueError('Non-unit or nonfinite actual '+semantic+': '+name)
        if not np.all(np.isfinite(master.accessor(p['attributes']['TEXCOORD_0']))):
            raise ValueError('Nonfinite actual UVs: '+name)
    body = np.concatenate([master.triangles(n)for n in master.meshes if n.startswith('CartBody_')or n=='central_reconstructed_reach'])
    clearances = []
    for name,source_node,side in [('wheel_fl_CartDetails_0',12,1),('wheel_fr_CartDetails_0',10,-1)]:
        wheel = master.positions(name)[np.unique(np.concatenate([c['indices']for c in source.components(source_node)[:9]]))]
        centre = master.translation('vehicle_wheel_front_'+('left'if side==1 else'right'))
        row = front_swept_clearance(body,wheel,centre,side,recipe['steering_limit_deg'])
        if row['minimum_gap_m']<=.005:
            raise ValueError('Actual continuous front-wheel/body clearance unproved: '+name)
        # Deliberately move the ACTUAL body into the wheel envelope. This must
        # defeat the separator; it does not certify an arbitrary solid collision.
        moved = body+np.array([side*.2,0,0])
        if front_swept_clearance(moved,wheel,centre,side,recipe['steering_limit_deg'])['minimum_gap_m']>0:
            raise ValueError('Intersecting-body negative control escaped clearance guard')
        clearances.append({'wheel':name,**row})
    # Real indexed support interfaces, not merely overlap of AABBs or arithmetic
    # repeated from the constructor. Positive surface intersections are intended
    # reconstructed axle/wood joinery, not a claim of engineered load capacity.
    bridge = master.triangles('central_drawbar_bearing')+master.translation('vehicle_steer_front')
    pole = master.triangles('single_reconstructed_pole')+master.translation('vehicle_tongue')
    axle = master.triangles('CartSteer_CartBase_0')+master.translation('vehicle_steer_front')
    joins = {'pole_to_bearing':len(intersections(pole,bridge)), 'bearing_to_axle':len(intersections(bridge,axle))}
    if not all(joins.values()):
        raise ValueError('Actual pole support is disconnected: '+str(joins))
    if intersections(pole+np.array([0,0,1]),bridge):
        raise ValueError('Detached-pole negative control still classified as joined')
    reach=master.triangles('central_reconstructed_reach')+master.translation('vehicle_reach')
    # The old body/frame remains one source mesh. Analyze the actual known
    # original components for the two declared end connections independently.
    body_positions=master.positions('CartBody_CartBase_0')
    front_bolster=body_positions[source.components(4)[23]['indices'].reshape(-1,3)]
    rear_axle=body_positions[source.components(4)[25]['indices'].reshape(-1,3)]
    reach_joins={'front_fixed_bolster':len(intersections(reach,front_bolster)),
                 'rear_axle':len(intersections(reach,rear_axle))}
    if not all(reach_joins.values()):
        raise ValueError('Actual central reach is disconnected: '+str(reach_joins))
    if intersections(reach+np.array([0,1,0]),front_bolster)or intersections(reach+np.array([0,1,0]),rear_axle):
        raise ValueError('Detached-reach negative control still classified as joined')
    pin=master.triangles('original_kingbolt')
    if len(pin)!=source.components(8)[5]['triangles']:
        raise ValueError('Named kingbolt does not own the actual source pin')
    # Retain the existing eighty/static-farm-box selection rather than silently
    # treating this isolated optical specimen as accepted production replacement.
    protected=json.loads((ROOT/'data/transport/studies/farm-box-protected.json').read_bytes())
    for row in protected['paths']:
        if sha(ROOT/row['path'])!=row['sha256']:
            raise ValueError('Protected existing wagon/placement changed: '+row['path'])
    canonical=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    regions=wagon_code_regions((ROOT/protected['yard_wagon_code']['path']).read_text())
    if {k:hashlib.sha256(v.encode()).hexdigest()for k,v in regions.items()}!=protected['yard_wagon_code']['regions']:
        raise ValueError('Existing static wagon code/dependencies changed')
    town=json.loads((ROOT/protected['town_wagons']['path']).read_bytes())
    logical={'wagons':town['wagons'],'town_wagon_rule':town['town_wagon_rule'],'wagons_refused':town['wagons_refused'],
             'form':{k:town['form'][k]for k in protected['town_wagons']['form_keys']}}
    if canonical(logical)!=protected['town_wagons']['sha256'] or len(town['wagons'])!=protected['town_wagons']['record_count']:
        raise ValueError('Existing static wagon/cart records, dimensions or eligibility changed')
    parked=json.loads((ROOT/protected['fine_wood_selection']['path']).read_bytes())
    logical={'model':parked['models']['wagon_w01'],'stands':[r for r in parked['scenes']['1835']if r['model']=='wagon_w01']}
    if canonical(logical)!=protected['fine_wood_selection']['sha256'] or len(logical['stands'])!=3:
        raise ValueError('Existing three fine-wood stands/model selection changed')
    web=ROOT/'renderers/web/transport/farm-box-master'
    export=json.loads((web/'EXPORT-RECEIPT.json').read_bytes())
    if export['input_sha256']!=sha(master_path) or export['parameters_sha256']!=sha(recipe_path) or export['exporter_sha256']!=sha(ROOT/'tools/transport/farm_box/export_lods.mjs'):
        raise ValueError('Web export is not bound to current source/recipe/exporter')
    if not export['lossless_prune']['exact_live_semantics_equal'] or not export['negative_controls']:
        raise ValueError('Missing actual paired-geometry preservation proof/negative controls')
    for row in export['lods']:
        if sha(web/row['file'])!=row['sha256'] or (web/row['file']).stat().st_size!=row['bytes']:
            raise ValueError('Delivered web LOD changed: '+row['file'])
        if not row['meshopt_decoded_exact_to_precompression'] or not row['webp_extension_declared_required'] or not row['lossless_delivery_cleanup']['oriented_paired_semantics_equal']:
            raise ValueError('Missing actual decoded web contract: '+row['file'])
        for m in row['texture_representations']['measured_loss']:
            if not m['alpha_exact'] or m['RMSE_RGB']>{'near':5,'mid':6,'far':8}[row['level']] or (m['normal_angles']and m['normal_angles']['max_deg']>1):
                raise ValueError('Declared texture error bound exceeded')
            if set(m['roles'])&{'Normal','MetallicRoughness','Occlusion'} and max(m['channel_max'])>2:
                raise ValueError('Data-map channel bound exceeded')
    if [r['level']for r in export['lods']]!=['near','mid','far'] or not export['lods'][0]['near_geometry_shader_attributes_exact_to_master']:
        raise ValueError('Missing exact near/genuine LOD family')
    if not export['lods'][1]['triangles']<=export['lods'][0]['triangles']*.75 or not export['lods'][2]['triangles']<=export['lods'][0]['triangles']*.6:
        raise ValueError('Declared genuine LOD reductions lost')
    print(json.dumps({'result':'PASS: exact licensed master/current exports/actual geometry contracts; photographic and world acceptance remain separate',
                      'source_sha256':SOURCE_SHA256,'master_sha256':sha(master_path),'clearances':clearances,'actual_joinery_surface_pairs':joins,
                      'web_bytes':sum(r['bytes']for r in export['lods']),'ground':ground,'actual_reach_surface_pairs':reach_joins,
                      'negative_controls':['actual body moved into wheel envelope rejected','actual pole disconnected from bearing rejected','actual reach detached from both axles rejected'],
                      'limits':'No axle/hub force, suspension, horses/harness, occupied interface or continuous general solid collision claim. Modern construction reference and reconstructed finish are not historic specimen evidence.'}))


if __name__=='__main__':
    main()
