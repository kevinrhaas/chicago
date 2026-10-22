# SPDX-License-Identifier: GPL-3.0-or-later
"""Original separate timber trestle under decoded C02 shaft undersides.

Dimensions/station/material are disclosed engineering reconstructions. No vehicle
vertices or transforms are changed. The top contact envelope is read from the
actual exact carriage and checked against all clipped shaft-face vertices.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

CAR_SHA='f02c6a4ed9537546d5576ac9d15b881ae684920d5233a62f83387b015bf5af39'


def decode(path):
    b=path.read_bytes(); magic,version,length=struct.unpack_from('<III',b)
    if (magic,version,length)!=(0x46546c67,2,len(b)):
        raise ValueError('Complete glTF2 carriage required')
    jl,jt=struct.unpack_from('<II',b,12)
    if jt!=0x4e4f534a:raise ValueError('JSON chunk required')
    d=json.loads(b[20:20+jl]);off=20+jl
    bl,bt=struct.unpack_from('<II',b,off)
    if bt!=0x004e4942 or off+8+bl!=len(b):raise ValueError('One binary chunk required')
    return b,d,b[off+8:]


def read(d,b,ai):
    a=d['accessors'][ai];v=d['bufferViews'][a['bufferView']]
    if a['type']!='VEC3' or a['componentType']!=5126 or 'byteStride'in v:
        raise ValueError('Expected existing unindexed Float32 positions')
    return np.frombuffer(b,dtype='<f4',offset=v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*3).reshape((-1,3)).astype(np.float64)


def matrix(n):
    x,y,z,w=n.get('rotation',[0,0,0,1]);m=np.eye(4)
    m[:3,:3]=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
    m[:3,:3]*=np.array(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
    return m


def at_plane(tris,z):
    out=[]
    for tri in tris:
        if tri[:,2].min()>z or tri[:,2].max()<z:continue
        for a,b in zip(tri,np.roll(tri,-1,axis=0)):
            if a[2]==z:out.append(a.copy())
            if (a[2]<z<b[2])or(b[2]<z<a[2]):
                t=(z-a[2])/(b[2]-a[2]);p=a+t*(b-a);p[2]=z;out.append(p)
    if not out:raise ValueError('No shaft section at chosen station')
    return np.array(out)


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--carriage',type=Path,required=True)
    cli.add_argument('--output',type=Path,required=True)
    args=cli.parse_args()
    raw,source,blob=decode(args.carriage)
    if hashlib.sha256(raw).hexdigest()!=CAR_SHA:raise ValueError('Exact parked carriage required')
    if args.output.exists():raise ValueError('Fresh output required')
    parents={c:i for i,n in enumerate(source['nodes'])for c in n.get('children',[])}
    shaft_nodes=[i for i,n in enumerate(source['nodes'])if 'mesh'in n and source['nodes'][parents[i]]['name']=='vehicle_drawgear' and source['meshes'][n['mesh']]['primitives'][0]['material']==1]
    if len(shaft_nodes)!=1:raise ValueError('Exact original timber drawgear owner required')
    i=shaft_nodes[0];n=source['nodes'][i];m=np.eye(4);j=i
    while True:
        m=matrix(source['nodes'][j])@m
        if j not in parents:break
        j=parents[j]
    p=source['meshes'][n['mesh']]['primitives'][0]
    pts=read(source,blob,p['attributes']['POSITION']);pts=pts@m[:3,:3].T+m[:3,3];tris=pts.reshape((-1,3,3))
    # Fixed original station and dimensions, no fitting search. Cast depth edges
    # before reading so the source certificate uses exactly serialized Z planes.
    station=2.8;depth=.075;z0=float(np.float32(station-depth/2));z1=float(np.float32(station+depth/2))
    ends=[at_plane(tris,z)for z in [z0,z1]]
    for points in ends:
        if not(np.any(points[:,0]<-.25)and np.any(points[:,0]>.25)):
            raise ValueError('Both original shafts must cross the support depth')
    tops=[float(np.nextafter(np.float32(points[:,1].min()),np.float32(-np.inf)))for points in ends]
    top=lambda z:tops[0]+(tops[1]-tops[0])*(z-z0)/(z1-z0)
    clipped=list(ends)
    inside=pts[(pts[:,2]>=z0)&(pts[:,2]<=z1)]
    if len(inside):clipped.append(inside)
    clipped=np.concatenate(clipped)
    clearance=clipped[:,1]-np.array([top(z)for z in clipped[:,2]])
    if clearance.min()<0:raise ValueError('Crossbar top would cross an actual shaft surface')
    # On a triangle, Y-minus-top(Z) is affine. Plane intersections and original
    # in-slab vertices are its extrema, so this checks the entire clipped faces.
    vout=[];nout=[];parts=[]
    def mesh(name,v,faces):
        start=len(vout)//3
        for face in faces:
            for k in range(1,len(face)-1):
                t=np.array([v[x]for x in [face[0],face[k],face[k+1]]],dtype=np.float64)
                normal=np.cross(t[1]-t[0],t[2]-t[0]);norm=np.linalg.norm(normal)
                if norm<=1e-15:raise ValueError('Degenerate authored timber face')
                normal/=norm;vout.extend(t);nout.extend([normal]*3)
        parts.append({'name':name,'triangle_start':start,'triangle_count':len(vout)//3-start})
    boxfaces=[[0,3,2,1],[4,5,6,7],[0,4,7,3],[1,2,6,5],[3,7,6,2],[0,1,5,4]]
    def box(name,lo,hi):
        x,y,z=lo;X,Y,Z=hi
        mesh(name,[[x,y,z],[X,y,z],[X,Y,z],[x,Y,z],[x,y,Z],[X,y,Z],[X,Y,Z],[x,Y,Z]],boxfaces)
    # Crossbar's lower face is horizontal; its upper surface follows the decoded
    # lower envelope. Leave original vehicle geometry untouched.
    width=1.08;bar_h=.08;bottom=float(np.float32(min(tops)-bar_h))
    mesh('crossbar',[[-width/2,bottom,z0],[width/2,bottom,z0],[width/2,tops[0],z0],[-width/2,tops[0],z0],[-width/2,bottom,z1],[width/2,bottom,z1],[width/2,tops[1],z1],[-width/2,tops[1],z1]],boxfaces)
    # Two grounded transverse feet and two slightly splayed closed timber legs.
    for side in [-1,1]:
        x=side*.40
        box('foot_left'if side<0 else'foot_right',[x-.065,0,station-.17],[x+.065,.045,station+.17])
        a=np.array([side*.40,.045,station]);b=np.array([side*.34,bottom,station])
        u=b-a;u/=np.linalg.norm(u);v=np.array([0.,0.,.0275]);q=np.cross(u,v)
        vv=[(p+sx*v+sy*q).tolist()for p in [a,b]for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        # The beam end axes use a closed box ordering shared by both splayed legs.
        beamfaces=[[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]
        # Reorient each original face by its actual solid centroid.
        vv=np.array(vv);center=vv.mean(axis=0)
        for f in beamfaces:
            normal=np.cross(vv[f[1]]-vv[f[0]],vv[f[2]]-vv[f[0]])
            if np.dot(normal,vv[f].mean(axis=0)-center)<0:f.reverse()
        mesh('splayed_leg_left'if side<0 else'splayed_leg_right',vv,beamfaces)
    pos=np.array(vout,dtype='<f4');norm=np.array(nout,dtype='<f4')
    if len(pos)!=180 or pos[:,1].min()!=0:raise ValueError('Expected exactly60 grounded triangles')
    b=pos.tobytes()+norm.tobytes();views=[{'buffer':0,'byteOffset':0,'byteLength':pos.nbytes,'target':34962},{'buffer':0,'byteOffset':pos.nbytes,'byteLength':norm.nbytes,'target':34962}]
    extra={'asset_id':'carriage_shaft_rest_1904_reconstructed_01','license':'GPL-3.0-or-later','scene_year':1904,'confidence':'reconstructed','units':'m','up_axis':'+Y','forward_axis':'+Z','root_datum':'Same ground midpoint-between-axles datum as exact carriage; transform both together','carriage_sha256':CAR_SHA,'original_carriage_bytes_changed':False,'dimensions':{'station_z_m':station,'crossbar_width_m':width,'crossbar_depth_m':z1-z0,'crossbar_bottom_y_m':bottom,'crossbar_top_y_at_depth_ends_m':tops,'feet_width_m':.13,'feet_fore_aft_length_m':.34,'feet_height_m':.045,'leg_width_m':.055},'source_fit':{'owner':n['name'],'position_accessor':p['attributes']['POSITION'],'section_z_planes_m':[z0,z1],'full_clipped_triangle_vertex_checks':len(clipped),'minimum_signed_nonpenetration_m':float(clearance.min()),'contact_scope':'Crossbar is at or below every original clipped shaft triangle; microscopic float32-rounding gap is deliberate','original_section_min_y_m':[float(x[:,1].min())for x in ends]},'parts':parts,'statistics':{'triangles':60,'meshes':1},'liberty':'The timber trestle form, dimensions, position, color and use here are original unmeasured engineering reconstruction, not a manufacturer or archival hardware identification. No force/load/stability acceptance.'}
    d={'asset':{'version':'2.0','generator':'Chicago4D original deterministic timber shaft rest'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'name':'carriage_shaft_rest_root','mesh':0}],'meshes':[{'name':'original_timber_trestle','primitives':[{'attributes':{'POSITION':0,'NORMAL':1},'material':0}]}],'materials':[{'name':'reconstructed_unpainted_timber','pbrMetallicRoughness':{'baseColorFactor':[.15,.075,.028,1],'metallicFactor':0,'roughnessFactor':.76}}],'accessors':[{'bufferView':0,'componentType':5126,'count':len(pos),'type':'VEC3','min':pos.min(axis=0).tolist(),'max':pos.max(axis=0).tolist()},{'bufferView':1,'componentType':5126,'count':len(norm),'type':'VEC3'}],'bufferViews':views,'buffers':[{'byteLength':len(b)}],'extras':extra}
    j=json.dumps(d,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b+=b'\0'*((-len(b))%4)
    data=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b
    args.output.mkdir(parents=True)
    (args.output/'shaft-rest.glb').write_bytes(data)
    (args.output/'shaft-rest.json').write_text(json.dumps(extra,indent=2)+'\n')
    print(json.dumps({'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'minimum_shaft_clearance_m':float(clearance.min()),'triangles':60,'top':tops}))


if __name__=='__main__':main()
