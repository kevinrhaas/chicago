#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""A reproducible, credited, articulated adaptation of the licensed Old Cart.

The original appearance/UVs/maps survive. Metric dimensions, source-pose
neutralisation and the single pole are explicit Chicago reconstructions.
This producer does not change any existing placed wagon or claim photo approval.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

import numpy as np

from licensed_source import Source, SOURCE_SHA256, fixed_matmul

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT/'assets/authored/transport/farm_box_master_v1/old-cart-original.glb'


def normalized(a):
    length = np.linalg.norm(a, axis=1)
    if not np.all(np.isfinite(a)) or np.any(length <= 1e-12):
        raise ValueError('Invalid transformed direction')
    return a/length[:, None]


def tyre_centre(source, node):
    ring = source.components(node)[0]
    return (ring['min']+ring['max'])/2


def canonical_reconstructed_positions(positions):
    """Emit the reconstructed timber consistently across BLAS kernels.

    A picometre grid removes floating-point accumulation noise before float32
    storage and the exact bound receipts; it does not relax a reader contract.
    Normalize signed zero too, since freshness compares the emitted bytes.
    """
    positions = np.round(positions, decimals=12)
    positions[positions == 0] = 0.0
    return positions


def make(recipe):
    source = Source(SOURCE)
    g = copy.deepcopy(source.gltf)
    binary = bytearray(source.binary)
    body_min = source.positions(4).min(axis=0)
    body_max = source.positions(4).max(axis=0)
    floor_parts = source.components(4)[5:11]
    floor_y = float(max(x['max'][1] for x in floor_parts))
    front_centres = np.array([tyre_centre(source, i) for i in [10, 12]])
    rear_centres = np.array([tyre_centre(source, i) for i in [14, 16]])
    front_centre, rear_centre = front_centres.mean(axis=0), rear_centres.mean(axis=0)
    axle = front_centres[1]-front_centres[0]
    source_turn = math.atan2(-axle[0], axle[2])
    c, s = math.cos(source_turn), math.sin(source_turn)
    unsteer = np.array([[c,0,s],[0,1,0],[-s,0,c]])
    # +sourceZ -> +canonicalX; -sourceX -> +canonicalZ; +Y remains up.
    axes = np.array([[0,0,1],[0,1,0],[-1,0,0]], dtype=np.float64)
    length, width, height = recipe['body_m']
    bed = recipe['bed_top_m']
    halftrack = recipe['wheel_center_track_m']/2
    sx = width/(body_max[2]-body_min[2])
    middle_z = (body_min[2]+body_max[2])/2
    top_scale = height/(body_max[1]-floor_y)
    fx, rx = front_centre[0], rear_centre[0]
    source_axle_y = (front_centre[1]+rear_centre[1])/2
    front_z, rear_z = recipe['axle_stations_z_m']['front'], recipe['axle_stations_z_m']['rear']
    front_radius, rear_radius = recipe['wheel_radius_m']['front'], recipe['wheel_radius_m']['rear']
    anchors_x = [body_min[0], fx, rx, body_max[0]]
    anchors_z = [length/2, front_z, rear_z, -length/2]
    if not all(anchors_x[k] < anchors_x[k+1] for k in range(3)):
        raise ValueError('Source axle order changed')
    if [len(source.components(n)) for n in [4,5,7,8,10,12,14,16]] != [32,111,3,14,12,12,12,12]:
        raise ValueError('Source component ownership changed')

    def body_map(points):
        out = np.empty_like(points)
        jacobians = np.zeros((len(points),3,3))
        out[:,0] = (points[:,2]-middle_z)*sx
        jacobians[:,0,2] = sx
        for i, (x, y, _) in enumerate(points):
            segment = max(0,min(2,int(np.searchsorted(anchors_x,x,side='right'))-1))
            dz = (anchors_z[segment+1]-anchors_z[segment])/(anchors_x[segment+1]-anchors_x[segment])
            out[i,2] = anchors_z[segment]+(x-anchors_x[segment])*dz
            jacobians[i,2,0] = dz
            if y >= floor_y:
                out[i,1] = bed+(y-floor_y)*top_scale
                jacobians[i,1,1] = top_scale
            else:
                # The floor stays at the old .95m. Beneath it the actual source
                # frame connects to front/rear wheels at their distinct radii.
                fraction = (x-fx)/(rx-fx)
                axle_y = front_radius+fraction*(rear_radius-front_radius)
                scale = (bed-axle_y)/(floor_y-source_axle_y)
                out[i,1] = bed+(y-floor_y)*scale
                jacobians[i,1,1] = scale
                jacobians[i,1,0] = -(y-floor_y)*(rear_radius-front_radius)/(rx-fx)/(floor_y-source_axle_y)
        return out, jacobians

    nodes, meshes, receipts = [], [], []

    def node(name,parent=None,position=(0,0,0)):
        index = len(nodes)
        nodes.append({'name':name,'translation':list(position)})
        if parent is not None:
            nodes[parent].setdefault('children',[]).append(index)
        return index

    root = node('vehicle_root')
    body = node('vehicle_body',root)
    rear = node('vehicle_running_gear_rear',root,(0,rear_radius,rear_z))
    front = node('vehicle_steer_front',root,(0,front_radius,front_z))
    kingbolt = node('vehicle_kingbolt',front)
    reach = node('vehicle_reach',body)
    tongue = node('vehicle_tongue',front,(0,0,.35))
    wheels = {}
    for end,parent in [('front',front),('rear',rear)]:
        for side in ['left','right']:
            wheels[end,side] = node('vehicle_wheel_'+end+'_'+side,parent,((1 if side == 'left' else -1)*halftrack,0,0))

    def append_attribute(values):
        values = np.ascontiguousarray(values,dtype='<f4')
        if not np.all(np.isfinite(values)):
            raise ValueError('Nonfinite adapted attribute')
        binary.extend(b'\0'*(-len(binary)%4))
        g['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':values.nbytes,'target':34962})
        binary.extend(values.tobytes())
        g['accessors'].append({'bufferView':len(g['bufferViews'])-1,'componentType':5126,
                               'count':len(values),'type':f'VEC{values.shape[1]}',
                               'min':values.min(axis=0).astype(float).tolist(),
                               'max':values.max(axis=0).astype(float).tolist()})
        return len(g['accessors'])-1

    def append_indices(values):
        values = np.ascontiguousarray(values,dtype='<u4')
        binary.extend(b'\0'*(-len(binary)%4))
        g['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':values.nbytes,'target':34963})
        binary.extend(values.tobytes())
        g['accessors'].append({'bufferView':len(g['bufferViews'])-1,'componentType':5125,'count':len(values),'type':'SCALAR',
                               'min':[int(values.min())],'max':[int(values.max())]})
        return len(g['accessors'])-1

    def emit(source_node, frame, positions, jacobians, indices=None, name=None, ownership=None):
        original = source.primitive(source_node)
        primitive = copy.deepcopy(original)
        original_indices = source.accessor(original['indices']).reshape(-1)
        selected_indices = original_indices if indices is None else indices
        selected_vertices = np.unique(selected_indices)
        world_normals = source.world_directions(source_node,'NORMAL')
        world_tangents = source.world_directions(source_node,'TANGENT')
        uv_values = source.accessor(original['attributes']['TEXCOORD_0'])
        if indices is not None:
            # Actual exported accessor bounds must describe only this part.
            # Keeping unused shaft vertices would give GLTFLoader a phantom
            # bounding box even though the triangles never referenced them.
            positions = positions[selected_vertices]
            jacobians = jacobians[selected_vertices]
            world_normals = world_normals[selected_vertices]
            world_tangents = world_tangents[selected_vertices]
            uv_values = uv_values[selected_vertices]
            primitive['attributes']['TEXCOORD_0'] = append_attribute(uv_values)
            primitive['indices'] = append_indices(np.searchsorted(selected_vertices,selected_indices))
        primitive['attributes']['POSITION'] = append_attribute(positions)
        inverse = np.linalg.inv(jacobians)
        normals = normalized(np.einsum('ni,nij->nj',world_normals,inverse))
        tangent_xyz = normalized(np.einsum('nij,nj->ni',jacobians,world_tangents[:,:3]))
        tangent_xyz = normalized(tangent_xyz-normals*np.sum(tangent_xyz*normals,axis=1)[:,None])
        primitive['attributes']['NORMAL'] = append_attribute(normals)
        primitive['attributes']['TANGENT'] = append_attribute(np.c_[tangent_xyz,world_tangents[:,3]])
        used = positions[selected_vertices] if indices is None else positions
        mesh_name = name or source.gltf['nodes'][source_node]['name']
        meshes.append({'name':mesh_name,'primitives':[primitive]})
        ni = node(mesh_name,frame)
        nodes[ni]['mesh'] = len(meshes)-1
        receipts.append({'name':mesh_name,'original_node':source_node,'frame':nodes[frame]['name'],
                         'triangles':len(selected_indices)//3,
                         'source_UV_values_unchanged':True,
                         'source_UV_accessor_unchanged':primitive['attributes']['TEXCOORD_0']==original['attributes']['TEXCOORD_0'],
                         'subset_compacted':indices is not None,
                         'UV_values_sha256':hashlib.sha256(np.ascontiguousarray(uv_values,dtype='<f4').tobytes()).hexdigest(),
                         'source_material_unchanged':primitive['material']==original['material'],
                         'local_min_m':used.min(axis=0).tolist(),'local_max_m':used.max(axis=0).tolist(),
                         'ownership':ownership})

    for n in [4,5]:
        positions,jacobian = body_map(source.positions(n))
        emit(n,body,positions,jacobian,ownership='All artist-authored body/frame components; explicit continuous metric adaptation')

    front_rotation = fixed_matmul(axes, unsteer)
    # Source-pose neutralisation is separate from dimensional calibration.
    # Radial X/Y source directions have one common scale, so circles stay circles.
    for n in [7,8]:
        radial = front_radius/((source.components(10)[0]['max'][1]-source.components(10)[0]['min'][1])/2)
        matrix = fixed_matmul(np.diag([sx,radial,radial]), front_rotation)
        positions = fixed_matmul(source.positions(n)-front_centre, matrix.T)
        jacobian = np.repeat(matrix[None,:,:],len(positions),axis=0)
        indices = source.components(7)[0]['indices'] if n == 7 else np.concatenate([p['indices']for i,p in enumerate(source.components(8))if i!=5])
        emit(n,front,positions,jacobian,indices=indices,ownership='Neutralised front gear; original two shaft components excluded from this frame')
        if n == 8:
            emit(n,kingbolt,positions,jacobian,indices=source.components(8)[5]['indices'],
                 name='original_kingbolt',ownership='Actual source kingbolt component5 separately owned; retained4.994mm eccentricity, no exactcoaxial/strengthclaim')

    for source_node,end,side in [(10,'front','right'),(12,'front','left'),(14,'rear','left'),(16,'rear','right')]:
        centre = tyre_centre(source,source_node)
        radius = recipe['wheel_radius_m'][end]
        ring = source.components(source_node)[0]
        radial_scale = radius/((ring['max'][1]-ring['min'][1])/2)
        rotation = front_rotation if end == 'front' else axes
        # Use the original tyre section; width is reconstructed to70mm without
        # distorting the wheel's radial plane or changing its eight spokes/UVs.
        neutral = fixed_matmul(source.positions(source_node)-centre, rotation.T)
        ring_neutral = neutral[np.unique(ring['indices'])]
        axial_scale = .07/np.ptp(ring_neutral[:,0])
        matrix = fixed_matmul(np.diag([axial_scale,radial_scale,radial_scale]), rotation)
        positions = fixed_matmul(source.positions(source_node)-centre, matrix.T)
        emit(source_node,wheels[end,side],positions,np.repeat(matrix[None,:,:],len(positions),axis=0),
             ownership='Original eight-spoke wheel; circular radial calibration, tyre width and axle-centre frame reconstructed')

    # The single W01 pole replaces the source's pair of shafts. Reorient one
    # exact artist-authored shaft component through its principal timber axis;
    # original surface/UV/material ownership is retained, no painted proxy.
    shaft = source.components(7)[1]
    shaft_points = source.positions(7)
    selected = shaft_points[np.unique(shaft['indices'])]
    centre = selected.mean(axis=0)
    _,_,basis = np.linalg.svd(selected-centre,full_matrices=False)
    forward = basis[0]
    if forward[0] > 0:
        forward = -forward
    left = np.cross(np.array([0.,1.,0.]),forward)
    left /= np.linalg.norm(left)
    up = np.cross(forward,left)
    orientation = np.array([left,up,forward])
    local = fixed_matmul(shaft_points-centre, orientation.T)
    bounds = local[np.unique(shaft['indices'])]
    scale = np.array([.055/np.ptp(bounds[:,0]),.055/np.ptp(bounds[:,1]),recipe['tongue_length_m']/np.ptp(bounds[:,2])])
    matrix = fixed_matmul(np.diag(scale), orientation)
    positions = fixed_matmul(shaft_points-centre, matrix.T)
    positions[:,0] -= np.mean([bounds[:,0].min(),bounds[:,0].max()])*scale[0]
    positions[:,1] -= np.mean([bounds[:,1].min(),bounds[:,1].max()])*scale[1]
    positions[:,2] -= bounds[:,2].min()*scale[2]
    positions = canonical_reconstructed_positions(positions)
    emit(7,tongue,positions,np.repeat(matrix[None,:,:],len(positions),axis=0),indices=shaft['indices'],
         name='single_reconstructed_pole',ownership='Source shaft component1 adapted to existing W01 single-pole envelope; source component2 omitted')

    # The source paired shafts used separate outside bearings. A central W01
    # pole must have a real connection, not stop108mm ahead of the axle. Reuse
    # the same credited timber surface as a short central drawbar through the
    # axle, overlapping the pole at its articulated root. This is reconstructed
    # joinery; neither strength nor a historical hitch is asserted.
    bridge_scale = np.array([.10/np.ptp(bounds[:,0]),.08/np.ptp(bounds[:,1]),.55/np.ptp(bounds[:,2])])
    bridge_matrix = fixed_matmul(np.diag(bridge_scale), orientation)
    bridge = fixed_matmul(shaft_points-centre, bridge_matrix.T)
    bridge[:,0] -= np.mean([bounds[:,0].min(),bounds[:,0].max()])*bridge_scale[0]
    bridge[:,1] -= np.mean([bounds[:,1].min(),bounds[:,1].max()])*bridge_scale[1]
    bridge[:,2] -= bounds[:,2].min()*bridge_scale[2]+.10
    bridge = canonical_reconstructed_positions(bridge)
    emit(7,front,bridge,np.repeat(bridge_matrix[None,:,:],len(bridge),axis=0),indices=shaft['indices'],
         name='central_drawbar_bearing',ownership='Reconstructed central axle-to-pole support from reused licensed timber surface; designed joinery overlap at axle and pole root')

    # A reusable farm-box running gear needs an actual longitudinal coupling
    # reach, not an empty named interface or a body stringer relabeled as one.
    # Its source is the same credited timber component; metric fit is explicitly
    # reconstructed. Endpoints meet the actual fixed front plate/cross bolster
    # and rear axle seen in the emitted source-derived frame. The reach stays
    # with the body; only the lower bogie/kingbolt/tongue turn together.
    reach_front=np.array([0.,recipe['reach_endpoint_y_m']['front'],front_z])
    reach_rear=np.array([0.,recipe['reach_endpoint_y_m']['rear'],rear_z])
    reach_forward=reach_front-reach_rear
    reach_length=float(np.linalg.norm(reach_forward));reach_forward/=reach_length
    reach_left=np.array([1.,0.,0.]);reach_up=np.cross(reach_forward,reach_left)
    target_basis=np.column_stack([reach_left,reach_up,reach_forward])
    reach_scale=np.array([recipe['reach_section_m'][0]/np.ptp(bounds[:,0]),recipe['reach_section_m'][1]/np.ptp(bounds[:,1]),reach_length/np.ptp(bounds[:,2])])
    reach_matrix=fixed_matmul(fixed_matmul(target_basis, np.diag(reach_scale)), orientation)
    local_centre=(bounds.min(axis=0)+bounds.max(axis=0))/2
    reach_positions=fixed_matmul(shaft_points-centre, reach_matrix.T)-fixed_matmul(target_basis, local_centre*reach_scale)+(reach_front+reach_rear)/2
    reach_positions = canonical_reconstructed_positions(reach_positions)
    emit(7,reach,reach_positions,np.repeat(reach_matrix[None,:,:],len(reach_positions),axis=0),indices=shaft['indices'],
         name='central_reconstructed_reach',ownership='New actual longitudinal reach from licensed source timber component; reconstructed90x55mmsection and fixed front-plate/rear-axle fit, no historical orstrengthcertification')

    for name,parent,position in [('vehicle_hitch_team',tongue,(0,0,recipe['tongue_length_m'])),
                                 ('vehicle_hitch_single',front,(0,0,.35)),
                                 ('vehicle_seat_driver',body,(0,1.15,1.1)),
                                 ('vehicle_seat_passenger_01',body,(0,1.15,-.45)),
                                 ('vehicle_board_left',body,(.85,0,.5)),
                                 ('vehicle_board_right',body,(-.85,0,.5)),
                                 ('vehicle_camera_ride',body,(0,1.8,.2)),
                                 ('vehicle_collision',root,(0,0,0))]:
        node(name,parent,position)

    source_image_hashes = []
    for image in source.gltf['images']:
        v = source.gltf['bufferViews'][image['bufferView']]
        source_image_hashes.append(hashlib.sha256(source.binary[v['byteOffset']:v['byteOffset']+v['byteLength']]).hexdigest())
    sidecar = {'schema':'chicago_licensed_farm_box_master_v1','asset_id':recipe['asset_id'],
               'units':'m','up_axis':'+Y','forward_axis':'+Z','left_axis':'+X','grade':'reconstructed',
               'photographic_acceptance':False,'status':'Development master; matched-view, clearance, LOD and world qualification pending',
               'source':{'title':'Old Cart','author':'Lyskilde / longtail','license':'CC-BY-4.0',
                         'url':'https://sketchfab.com/3d-models/old-cart-f536745fd82144eeb5cc4900a48e816e',
                         'original_sha256':SOURCE_SHA256,'original_binary_prefix_preserved':True,
                         'embedded_image_sha256':source_image_hashes,'materials_exact':True,
                         'geometry_license':'CC-BY-4.0; original credit and adaptation notice retained',
                         'producer_code_license':'GPL-3.0-or-later; does not replace the source geometry license'},
               'parameters':recipe,'source_steering_neutralised_deg':math.degrees(source_turn),
               'source_floor_y':floor_y,'source_front_axle_centre':front_centre.tolist(),
               'source_rear_axle_centre':rear_centre.tolist(),'source_body_bounds':[body_min.tolist(),body_max.tolist()],
               'parts':receipts,'statistics':{'triangles':sum(x['triangles'] for x in receipts),'draw_batches':len(meshes)},
               'socket_policy':'Named proposed unloaded interfaces; no occupied seat, draft hitch, load, boarding or collision qualification',
               'limitations':recipe['source_limits']}
    g['asset']['generator'] = 'Chicago original articulated metric adaptation; licensed Old Cart appearance'
    g['asset']['copyright'] = 'Old Cart by Lyskilde/longtail, CC BY4.0; modifications by Chicago reconstruction project'
    # Keep original embedded author/license/source extras verbatim.
    g['extras'] = sidecar
    g['nodes'],g['meshes'],g['scenes'],g['scene'] = nodes,meshes,[{'nodes':[root]}],0
    binary.extend(b'\0'*(-len(binary)%4))
    g['buffers'] = [{'byteLength':len(binary)}]
    encoded = json.dumps(g,separators=(',',':'),allow_nan=False).encode()
    encoded += b' '*(-len(encoded)%4)
    raw = (struct.pack('<III',0x46546c67,2,28+len(encoded)+len(binary))
           +struct.pack('<II',len(encoded),0x4e4f534a)+encoded
           +struct.pack('<II',len(binary),0x004e4942)+binary)
    return raw,sidecar


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--parameters',type=Path,required=True)
    cli.add_argument('--output-dir',type=Path,required=True)
    cli.add_argument('--verify',action='store_true')
    args = cli.parse_args()
    recipe = json.loads(args.parameters.read_text())
    if not args.verify and args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise ValueError('Fresh output directory required')
    raw,sidecar = make(recipe)
    sidecar['glb_sha256'] = hashlib.sha256(raw).hexdigest()
    products={'farm-box-source.glb':raw,'farm-box-source.json':(json.dumps(sidecar,indent=2)+'\n').encode()}
    if args.verify:
        for name,data in products.items():
            if not (args.output_dir/name).is_file() or (args.output_dir/name).read_bytes()!=data:
                raise ValueError('Stale or missing authored output '+name)
    else:
        args.output_dir.mkdir(parents=True,exist_ok=True)
        for name,data in products.items():
            (args.output_dir/name).write_bytes(data)
    print(json.dumps({'bytes':len(raw),'sha256':sidecar['glb_sha256'],**sidecar['statistics'],
                      'source_steering_neutralised_deg':sidecar['source_steering_neutralised_deg']}))


if __name__ == '__main__':
    main()
