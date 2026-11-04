#!/usr/bin/env python3
"""Portable unit geometry, instanced between live measured hitch endpoints."""
from pathlib import Path
import json,math,numpy as np
from build_hitch_prototype import write_glb,sha,HERE
params={'schema':'portable_draft_connection_units_v1','unit_length_axis':'+Z','unit_length_m':1,'units':[
    {'name':'unit_trace','kind':'box','width_m':.025,'thickness_m':.004,'material':'leather'},
    {'name':'unit_rein','kind':'box','width_m':.008,'thickness_m':.003,'material':'leather'},
    {'name':'unit_wood_bar','kind':'cylinder','radius_m':.025,'radial_segments':8,'material':'wood'},
    {'name':'unit_iron_link','kind':'cylinder','radius_m':.006,'radial_segments':8,'material':'iron'}],
    'policy':'Original reconstructed geometry. Unitprimitivesareinstancedbetweenactualsource-bound liveendpoints. No loadstrength, historicalconstruction or bodycontactcertification.'}
p=HERE/'connection-unit-parameters.json'
if p.exists():assert json.loads(p.read_text())==params
else:p.write_text(json.dumps(params,indent=2)+'\n')
materials=[{'name':'reconstructed_draft_leather','pbrMetallicRoughness':{'baseColorFactor':[.09,.045,.022,1],'metallicFactor':0,'roughnessFactor':.85}},
{'name':'reconstructed_hitch_wood','pbrMetallicRoughness':{'baseColorFactor':[.25,.145,.065,1],'metallicFactor':0,'roughnessFactor':.8}},
{'name':'reconstructed_hitch_iron','pbrMetallicRoughness':{'baseColorFactor':[.08,.075,.068,1],'metallicFactor':.75,'roughnessFactor':.7}}]
mi={'leather':0,'wood':1,'iron':2};arrays=[];meshes=[];nodes=[];total=0
for unit in params['units']:
    P=[];N=[];F=[]
    def quad(points,normal):
        k=len(P);P.extend(points);N.extend([normal]*4);F.extend([[k,k+1,k+2],[k,k+2,k+3]])
    if unit['kind']=='box':
        x=unit['width_m']/2;y=unit['thickness_m']/2
        quad([[-x,-y,0],[-x,y,0],[x,y,0],[x,-y,0]],[0,0,-1]);quad([[-x,-y,1],[x,-y,1],[x,y,1],[-x,y,1]],[0,0,1])
        quad([[-x,-y,0],[x,-y,0],[x,-y,1],[-x,-y,1]],[0,-1,0]);quad([[-x,y,0],[-x,y,1],[x,y,1],[x,y,0]],[0,1,0])
        quad([[-x,-y,0],[-x,-y,1],[-x,y,1],[-x,y,0]],[-1,0,0]);quad([[x,-y,0],[x,y,0],[x,y,1],[x,-y,1]],[1,0,0])
    else:
        n=unit['radial_segments'];r=unit['radius_m']
        for i in range(n):
            a=2*math.pi*i/n;b=2*math.pi*(i+1)/n;m=(a+b)/2
            quad([[r*math.cos(a),r*math.sin(a),0],[r*math.cos(b),r*math.sin(b),0],[r*math.cos(b),r*math.sin(b),1],[r*math.cos(a),r*math.sin(a),1]],[math.cos(m),math.sin(m),0])
            for z,normal,flip in [(0,[0,0,-1],True),(1,[0,0,1],False)]:
                k=len(P);points=[[0,0,z],[r*math.cos(a),r*math.sin(a),z],[r*math.cos(b),r*math.sin(b),z]]
                if flip:points=[points[0],points[2],points[1]]
                P.extend(points);N.extend([normal]*3);F.append([k,k+1,k+2])
    first=len(arrays);arrays.extend([(np.array(P,dtype='<f4'),'VEC3',5126),(np.array(N,dtype='<f4'),'VEC3',5126),(np.array(F,dtype='<u2').reshape(-1,1),'SCALAR',5123)])
    meshes.append({'name':unit['name'],'primitives':[{'attributes':{'POSITION':first,'NORMAL':first+1},'indices':first+2,'material':mi[unit['material']],'mode':4}]});nodes.append({'name':unit['name'],'mesh':len(meshes)-1});total+=len(F)
d={'asset':{'version':'2.0','generator':'build_connection_units.py','copyright':'Original reconstructed connection units; GPL-3.0-or-later'},'scene':0,'scenes':[{'nodes':list(range(len(nodes)))}],'nodes':nodes,'meshes':meshes,'materials':materials}
out=HERE/'draft-connection-units-SOURCE-PROTOTYPE.glb';write_glb(out,d,arrays)
result={'status':'GENERATED_CONNECTION_UNITS_ONLY_NOT_NATIVE_WORLD_ACCEPTANCE','path':str(out),'sha256':sha(out.read_bytes()),'bytes':out.stat().st_size,'unit_meshes':len(meshes),'triangles_if_each_once':total,'materials':len(materials),'images':0,'parameters_sha256':sha(p.read_bytes())}
(HERE/'GENERATED-CONNECTION-UNITS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
