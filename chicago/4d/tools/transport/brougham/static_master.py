# SPDX-License-Identifier: GPL-3.0-or-later
"""Original static master references derived from actual source geometry.

Conservative metadata only. No runtime collision, boarding, rein, door, occupant
or team coupling is enabled; proposed hand/foot frames are not human-fit proof.
"""
import math
import struct
from index_streams import attribute_rows


def static_master_contract(doc, binary, world, source_sha256):
    if len(source_sha256)!=64 or any(c not in '0123456789abcdef' for c in source_sha256):
        raise ValueError('Actual source hash required')
    parent={child:i for i,n in enumerate(doc['nodes']) for child in n.get('children',[])}
    named={n['name']:i for i,n in enumerate(doc['nodes']) if n['name'].startswith('vehicle_')}
    batches={};groups={}
    def points(prim,i):
        return [[v[k]+world[i][k] for k in range(3)] for raw in attribute_rows(doc,binary,prim['attributes']['POSITION']) for v in [struct.unpack('<fff',raw)]]
    def bound(ps):
        if not ps or not all(math.isfinite(v) for p in ps for v in p):raise ValueError('Finite nonempty source component required')
        return {'min':[min(p[k] for p in ps) for k in range(3)],'max':[max(p[k] for p in ps) for k in range(3)]}
    for i,n in enumerate(doc['nodes']):
        if 'mesh' not in n:continue
        frame=parent[i];group=frame
        while not doc['nodes'][group]['name'].startswith('vehicle_'):
            group=parent[group]
        name=doc['nodes'][group]['name']
        for prim in doc['meshes'][n['mesh']]['primitives']:
            ps=points(prim,i);key=(frame,prim['material'])
            if key in batches:raise ValueError('Expected one raw source batch per frame/material')
            batches[key]=ps;groups.setdefault(name,[]).extend(ps)
    parts=[]
    required_parts={'interior_floor','driver_footboard','rounded_empty_driver_cushion','door_step','deep_U_closed_door'}
    for index,p in enumerate(doc['extras']['parts']):
        if p['name'] not in required_parts:continue
        frames=[i for i,n in enumerate(doc['nodes']) if n['name']==p['frame']]
        if len(frames)!=1:raise ValueError('Unambiguous measured source part frame required')
        start=3*p['triangle_start_in_batch'];stop=start+3*p['triangles'];stream=batches[(frames[0],p['material'])]
        if not 0<=start<stop<=len(stream):raise ValueError('Source component range outside batch')
        parts.append({'part_index':index,'name':p['name'],'bounds_root_m':bound(stream[start:stop])})
    def selected(name):return [p for p in parts if p['name']==name]
    def side_part(name,sign):
        ps=[p for p in selected(name) if (p['bounds_root_m']['min'][0]+p['bounds_root_m']['max'][0])*sign>0]
        if len(ps)!=1:raise ValueError('One measured source '+name+' required per side')
        return ps[0]
    def one(name):
        ps=selected(name)
        if len(ps)!=1:raise ValueError('One source component required: '+name)
        return ps[0]['bounds_root_m']
    def center(b):return [(a+c)/2 for a,c in zip(b['min'],b['max'])]
    def frame(name):return list(world[named[name]])
    def target(name,p,basis,inward_side=0):
        return {'name':name,'parent':'vehicle_root','translation_root_m':p,'rotation_xyzw':[0,-inward_side*math.sqrt(.5),0,math.sqrt(.5)] if inward_side else [0,0,0,1],'grade':'reconstructed','basis':basis,'dynamic_binding_supported':False}
    floor=one('interior_floor');footboard=one('driver_footboard');driver=frame('vehicle_seat_driver');bench=one('rounded_empty_driver_cushion')
    anchors=[];entries=[]
    for side,sign in [('left',1),('right',-1)]:
        step=side_part('door_step',sign)
        door=side_part('deep_U_closed_door',sign)
        b=step['bounds_root_m'];c=center(b);c[1]=b['max'][1]
        anchors.extend([target('vehicle_step_reference_'+side,c,'Source tread-bounds upper-plane datum only; not a validated foot contact or traversable tread',sign),target('vehicle_boarding_'+side,[sign*(max(abs(b['min'][0]),abs(b['max'][0]))+.30),0,c[2]],'Original ground approach300mm outside source step extent; not an obstacle-cleared route',sign),target('vehicle_rein_'+side,[sign*(bench['max'][0]-bench['min'][0])*.15,driver[1]+.20,driver[2]+.30],'Original prospective driver hand target200mm above/300mm forward of seat datum; no rein fitting or human pose attested')])
        anchors.append(target('vehicle_door_entry_'+side,center(door['bounds_root_m']),'Closed lower-leaf bounds center facing inward; no door pivot or open passage',sign))
        entries.append({'side':side,'door_part_index':door['part_index'],'closed_door_bounds_root_m':door['bounds_root_m'],'step_part_index':step['part_index'],'step_bounds_root_m':b,'floor_bounds_root_m':floor,'ground_to_step_top_m':b['max'][1],'step_top_to_floor_top_m':floor['max'][1]-b['max'][1],'entry_aperture_available':False,'door_operation_supported':False,'hinge_and_sweep_clearance_validated':False,'note':'Closed door blocks entry; profile bounds and vertical rises are source geometry measurements, not an open aperture or feasible human passage'})
    seats=[]
    for name in ['vehicle_seat_driver','vehicle_seat_passenger_01','vehicle_seat_passenger_02']:
        p=frame(name)
        if name.endswith('driver'):
            feet=[[x,footboard['max'][1],center(footboard)[2]] for x in [-.16,.16]]
            surface=footboard
        else:
            feet=[[p[0]+x,floor['max'][1],max(floor['min'][2]+.05,min(floor['max'][2]-.05,p[2]+.55))] for x in [-.08,.08]]
            surface=floor
        seats.append({'node':name,'pelvis_reference_root_m':p,'prospective_feet_root_m':feet,'feet_reference_surface_bounds_root_m':surface,'fit_validated':False,'basis':'Existing seat datum; original prospective foot placement on measured floor/footboard only, not a portable-human pose'})
    return {'revision':'static_master_interfaces_v1','source_master_sha256':source_sha256,'frame':{'units':'m','up':'+Y','forward':'+Z','root':'vehicle_root'},'grade':'reconstructed','named_targets':anchors,'seats':seats,'entries':entries,'collision_proxy':{'kind':'compound_conservative_root_AABBs','components':[{'source_frame':n,'bounds_root_m':bound(ps)} for n,ps in sorted(groups.items())],'all_source_vertices_covered':True,'runtime_enabled':False,'purpose':'Coarse static obstacle candidate for later validation; includes closed glass/cabin and fills spoke/underbody gaps; not occupied containment, picking or physics'},'hitch':{'node':'vehicle_hitch_team','parked_translation_root_m':frame('vehicle_hitch_team'),'hitch_ready_pose_available':False,'team_coupling_supported':False,'note':'Measured static parked-down pole tip, not working-height coupling; no invented pole pivot or horse binding'},'door_geometry':{'owned_parts':['deep_U_closed_door','side_door_glass'],'independent_door_node_available':False,'hinge_axis_known':False},'capabilities':{k:False for k in ['driver_passenger_fit','boarding','rein_binding','door_operation','hitch_team_coupling','runtime_collision','steering_wheel_animation','traffic']},'limits':['All coordinates and dimensions not attested by catalogue remain reconstruction','No actual human, entry sweep, continuous clearance, animated collision or horse force/profile qualification','Metadata does not enable a visitor interaction or replace final static and photographic acceptance']}
