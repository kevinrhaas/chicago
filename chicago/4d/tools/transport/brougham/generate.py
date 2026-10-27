# SPDX-License-Identifier: GPL-3.0-or-later
"""Original source-bounded Studebaker1893 Brougham, static1904 reconstruction.

All dimensions and unseen construction are explicit engineering choices. The
actual1893 public-domain plate0095 bounds silhouette/features; no C02 rebadge.
No Blender or downloaded image/texture is used to generate the model.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import struct

import numpy as np

from source_details import feature_plan
from quarter_surface import quarter_surface
from body_finish import finished_materials, rounded_pad, curved_coach_panel, coach_front_wrap


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--parameters',type=Path,default=Path(__file__).with_name('parameters.json'))
    cli.add_argument('--output',type=Path,required=True)
    cli.add_argument('--detail',choices=['near','mid','far'],default='near')
    cli.add_argument('--lod-recipe',type=Path,default=Path(__file__).with_name('lods.json'))
    cli.add_argument('--rear-quarter-recipe',type=Path,default=None)
    a=cli.parse_args();p=json.loads(a.parameters.read_text())
    if a.rear_quarter_recipe is None and p.get('photo_finish_v19'):
        a.rear_quarter_recipe=Path(__file__).with_name('rear-quarter.json')
    quarter_recipe=None if a.rear_quarter_recipe is None else json.loads(a.rear_quarter_recipe.read_text())
    cabin_glass=7 if p.get('photo_finish_v19') else 5
    if a.output.exists():raise ValueError('Fresh output required')
    detail=json.loads(a.lod_recipe.read_text())['details'][a.detail]
    def lod_n(original,key):
        value=detail.get(key,original)
        if type(value) is not int or value<2:raise ValueError('Invalid LOD sample count '+key)
        return min(original,value)
    for key in ['wheelbase_m','track_m','front_wheel_radius_m','rear_wheel_radius_m','body_half_width_m']:
        if not isinstance(p[key],(int,float))or not math.isfinite(p[key])or p[key]<=0:raise ValueError('Invalid dimension '+key)
    nodes=[];batches={};parts=[]
    def node(name,parent=None,t=(0,0,0)):
        if name.startswith('vehicle_seat_'):
            shape=p['body_vertical_affine'];t=(t[0],t[1]*shape['scale_y']+shape['offset_y_m'],t[2])
        i=len(nodes);nodes.append({'name':name,'translation':list(t),'children':[]})
        if parent is not None:nodes[parent]['children'].append(i)
        return i
    root=node('vehicle_root');body=node('vehicle_body',root)
    def geometry(name,parent,vertices,faces,mat,smooth=False,normals_override=None):
        vs=np.array(vertices,dtype=np.float64,copy=True)
        if parent==body:
            shape=p['body_vertical_affine'];vs[:,1]=vs[:,1]*shape['scale_y']+shape['offset_y_m']
        tri=[]
        for face in faces:
            for k in range(1,len(face)-1):tri.append([face[0],face[k],face[k+1]])
        tri=np.asarray(tri,dtype=int);tt=vs[tri];nn=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);length=np.linalg.norm(nn,axis=1)
        if np.any(length<1e-13):raise ValueError('Degenerate original surface '+name)
        if normals_override is not None:
            vn=np.array(normals_override,dtype=np.float64,copy=True)
            if vn.shape!=vs.shape:raise ValueError('Analytical normal inventory differs')
            if parent==body:vn[:,1]/=p['body_vertical_affine']['scale_y']
            lengths=np.linalg.norm(vn,axis=1)
            if np.any(lengths<1e-12)or not np.isfinite(vn).all():raise ValueError('Invalid analytical normal')
            vn/=lengths[:,None];normals=vn[tri]
        elif smooth:
            vn=np.zeros_like(vs)
            if smooth=='angle':
                # The coach shell has irregular source-outline samples. Area
                # weights bias its normals toward the largest strip triangles;
                # corner angles keep a smooth surface independent of that fan.
                unit=nn/length[:,None]
                for k in range(3):
                    u=tt[:,(k+1)%3]-tt[:,k];v=tt[:,(k+2)%3]-tt[:,k]
                    cos=np.sum(u*v,axis=1)/(np.linalg.norm(u,axis=1)*np.linalg.norm(v,axis=1))
                    angle=np.arccos(np.clip(cos,-1.,1.))
                    np.add.at(vn,tri[:,k],unit*angle[:,None])
            else:
                for k in range(3):np.add.at(vn,tri[:,k],nn)
            vn/=np.linalg.norm(vn,axis=1)[:,None];normals=vn[tri]
        else:normals=np.repeat((nn/length[:,None])[:,None,:],3,axis=1)
        key=(parent,mat);entry=batches.setdefault(key,{'positions':[],'normals':[]})
        start=len(entry['positions'])//3;entry['positions'].extend(tt.reshape((-1,3)));entry['normals'].extend(normals.reshape((-1,3)))
        parts.append({'name':name,'frame':nodes[parent]['name'],'material':mat,'triangle_start_in_batch':start,'triangles':len(tri)})
    faces_box=[[0,3,2,1],[4,5,6,7],[0,4,7,3],[1,2,6,5],[3,7,6,2],[0,1,5,4]]
    def box(name,parent,center,size,mat):
        c=np.array(center);x,y,z=np.array(size)/2
        v=np.array([[-x,-y,-z],[x,-y,-z],[x,y,-z],[-x,y,-z],[-x,-y,z],[x,-y,z],[x,y,z],[-x,y,z]])+c
        geometry(name,parent,v,faces_box,mat)
    def beam(name,parent,start,end,width,mat,depth=None):
        start,end=np.array(start),np.array(end);u=end-start;u/=np.linalg.norm(u)
        ref=np.array([0.,1.,0.])if abs(u[1])<.9 else np.array([1.,0.,0.])
        v=np.cross(u,ref);v/=np.linalg.norm(v);v*=width/2;q=np.cross(u,v)
        if depth is not None:q*=depth/width
        vv=np.array([c+x*v+y*q for c in [start,end]for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]])
        ff=[[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]];center=vv.mean(axis=0)
        for f in ff:
            if np.dot(np.cross(vv[f[1]]-vv[f[0]],vv[f[2]]-vv[f[0]]),vv[f].mean(axis=0)-center)<0:f.reverse()
        geometry(name,parent,vv,ff,mat)
    def tube(name,parent,path,r,mat,sides=8):
        sides=lod_n(sides,'tube_sides');path=np.array(path,dtype=float);closed=bool(np.linalg.norm(path[0]-path[-1])<1e-10)
        if closed:path=path[:-1]
        tangents=[]
        for i in range(len(path)):
            u=(path[(i+1)%len(path)]-path[(i-1)%len(path)]) if closed else (path[min(i+1,len(path)-1)]-path[max(0,i-1)])
            tangents.append(u/np.linalg.norm(u))
        tangents=np.array(tangents)
        # One axis for the complete curve avoids discontinuous per-ring switches.
        ref=np.eye(3)[int(np.argmin(np.max(np.abs(tangents),axis=0)))];v=[]
        for c,u in zip(path,tangents):
            n=np.cross(u,ref);n/=np.linalg.norm(n);b=np.cross(u,n)
            v.extend([c+r*(math.cos(t)*n+math.sin(t)*b)for t in np.arange(sides)*math.tau/sides])
        f=[] if closed else [list(range(sides-1,-1,-1)),list(range((len(path)-1)*sides,len(path)*sides))]
        for i in range(len(path) if closed else len(path)-1):
            nxt=(i+1)%len(path)
            for j in range(sides):k=(j+1)%sides;f.append([i*sides+j,i*sides+k,nxt*sides+k,nxt*sides+j])
        # Face normals preserve sharp cap/barrel boundaries on these thin trim parts.
        geometry(name,parent,v,f,mat,smooth=False)
    def circle_tube(name,parent,radius,width,radial,mat,segments=80):
        # Elliptic cross-section rounded iron/wood rim; portable explicit normals.
        v=[];N=lod_n(segments,'ring_segments')
        # Keep the broad rounded hub cross section at its independently chosen
        # detail; thin tire/felloe/button rims may use the ring profile recipe.
        cross_key=('hub_ring_cross_sides' if name=='rounded_hub'
                   and 'hub_ring_cross_sides' in detail else 'ring_cross_sides')
        K=lod_n(8,cross_key)
        for j in range(N):
            theta=j*math.tau/N
            for k in range(K):
                phi=k*math.tau/K;rr=radius+radial*math.cos(phi)
                v.append([width/2*math.sin(phi),rr*math.cos(theta),rr*math.sin(theta)])
        f=[]
        for j in range(N):
            for k in range(K):f.append([j*K+k,((j+1)%N)*K+k,((j+1)%N)*K+(k+1)%K,j*K+(k+1)%K])
        # Winding outward is determined at each convex tube section.
        vv=np.array(v)
        for fi,f0 in enumerate(f):
            center=vv[f0].mean(axis=0);ring_center=np.array([0,radius*center[1]/np.linalg.norm(center[1:]),radius*center[2]/np.linalg.norm(center[1:])])
            if np.dot(np.cross(vv[f0[1]]-vv[f0[0]],vv[f0[2]]-vv[f0[0]]),center-ring_center)<0:f0.reverse()
        geometry(name,parent,v,f,mat,smooth=True)
    def solid_axial_body(name,parent,profile,mat,segments,side=1):
        segments=lod_n(segments,'hub_segments')
        # Original closed axial hub/button with real center faces, not a torus.
        # The profile is disclosed in parameters, not claimed as measured hardware.
        v=[]
        for x,radius in profile:
            for k in range(segments):
                t=k*math.tau/segments;v.append([side*x,radius*math.cos(t),radius*math.sin(t)])
        v.extend([[side*profile[0][0],0,0],[side*profile[-1][0],0,0]])
        f=[];rings=len(profile);start_center=rings*segments;end_center=start_center+1
        for k in range(segments):
            j=(k+1)%segments
            f.append([start_center,j,k]);f.append([end_center,(rings-1)*segments+k,(rings-1)*segments+j])
            for ring in range(rings-1):
                f.append([ring*segments+k,ring*segments+j,(ring+1)*segments+j,(ring+1)*segments+k])
        # Standard angular direction makes the left cap normal -X. Mirror the
        # entire closed surface coherently for the opposite wheel side.
        if side<0:f=[list(reversed(face))for face in f]
        # At a positive-radius midsegment the surface normal must be radial out.
        vv=np.array(v);probe=f[2];center=vv[probe].mean(axis=0)
        if np.dot(np.cross(vv[probe[1]]-vv[probe[0]],vv[probe[2]]-vv[probe[0]]),[0,center[1],center[2]])<0:
            f=[list(reversed(face))for face in f]
        geometry(name,parent,v,f,mat,smooth=True)
    def earclip(profile):
        q=np.array(profile,dtype=float)
        area=np.sum(q[:,0]*np.roll(q[:,1],-1)-q[:,1]*np.roll(q[:,0],-1))
        order=list(range(len(q)))if area>0 else list(range(len(q)-1,-1,-1));out=[]
        cross=lambda x,y,z:float((y[0]-x[0])*(z[1]-x[1])-(y[1]-x[1])*(z[0]-x[0]))
        while len(order)>3:
            found=False
            for k,b in enumerate(order):
                aa=order[k-1];c=order[(k+1)%len(order)]
                if cross(q[aa],q[b],q[c])<=1e-12:continue
                if any(j not in (aa,b,c)and min(cross(q[aa],q[b],q[j]),cross(q[b],q[c],q[j]),cross(q[c],q[aa],q[j]))>=-1e-12 for j in order):continue
                out.append([aa,b,c]);order.pop(k);found=True;break
            if not found:raise ValueError('Non-simple original profile')
        return out+[order]
    def profile_solid(name,parent,profile,side,width,thickness,mat):
        profile=np.array(profile);n=len(profile);w=np.array([width(y)if callable(width)else width for z,y in profile]);inner=side*w;outer=side*(w+thickness)
        lo=np.minimum(inner,outer);hi=np.maximum(inner,outer)
        v=[[lo[i],y,z]for i,(z,y)in enumerate(profile)]+[[hi[i],y,z]for i,(z,y)in enumerate(profile)]
        tt=earclip(profile);f=tt+[[n+k for k in reversed(t)]for t in tt]
        # Ear triangles have CCW(z,y), hence negativeX; derive ordered boundary.
        area=np.sum(profile[:,0]*np.roll(profile[:,1],-1)-profile[:,1]*np.roll(profile[:,0],-1));order=list(range(n))if area>0 else list(range(n-1,-1,-1))
        f.extend([[i,n+i,n+j,j]for i,j in zip(order,order[1:]+order[:1])])
        geometry(name,parent,v,f,mat)
    def catmull(points,steps=5,closed=False):
        q=np.array(points,dtype=float);out=[];n=len(q)
        for i in range(n if closed else n-1):
            v0=q[(i-1)%n]if closed else q[max(0,i-1)];v1=q[i];v2=q[(i+1)%n];v3=q[(i+2)%n]if closed else q[min(n-1,i+2)]
            for t in np.arange(steps)/steps:
                out.append(.5*((2*v1)+(-v0+v2)*t+(2*v0-5*v1+4*v2-v3)*t*t+(-v0+3*v1-3*v2+v3)*t*t*t))
        if not closed:out.append(q[-1])
        return np.array(out)

    WB=p['wheelbase_m'];TRACK=p['track_m'];RF=p['front_wheel_radius_m'];RR=p['rear_wheel_radius_m'];half=p['body_half_width_m']
    lower=catmull(p['lower_side_profile_z_y_m'][:-1],4).tolist()+[p['lower_side_profile_z_y_m'][-1]]
    width=lambda y:half-.18*max(0,min(1,(1.26-y)/.91))
    door=catmull(p['door_profile_z_y_m'],p['door_profile_sampling']['steps'],True).tolist()
    for side in [-1,1]:
        # T-3084: triangulate a sampled curved shell, not a warped side-cap fan.
        shell_vertices,shell_faces=curved_coach_panel(lower,side,width,.026,earclip,
                                                     segments=lod_n(4,'body_subdivisions'))
        geometry('deep_curved_lower_body',body,shell_vertices,shell_faces,0,smooth='angle')
        profile_solid('deep_U_closed_door',body,door,side,lambda y:width(y)+.034,.018,0)
        # Fine bright trim follows the actual newly authored U, not an old box.
        trace=[[side*(width(y)+.055),y,z]for z,y in door]
        trace.append(trace[0]);tube('door_edge_lining',body,trace,.0032,3,6)
        # Main glazed door with narrow central division and shaped upper rail.
        glassprof=p['side_door_glass_profile_z_y_m']
        profile_solid('side_door_glass',body,glassprof,side,half+.010,.009,cabin_glass)
        outline=[[side*(half+.027),y,z]for z,y in glassprof];outline.append(outline[0])
        tube('side_window_frame',body,outline,.013,1,8)
        dy0,dy1,dz=p['side_glass_division_y_y_z_m']
        beam('side_glass_division',body,(side*(half+.028),dy0,dz),(side*(half+.028),dy1,dz),.015,1)
        beam('rear_window_pillar',body,(side*(half+.013),1.315,-.398),(side*(half+.013),1.74,-.398),.090,1,depth=.025)
        # Bowed, solid rear quarter and narrow upper rear pillar.
        rearprof=[[-.45,1.28],[-.44,1.69],[-.61,1.72],[-1.04,1.70],[-1.09,1.54],[-1.08,1.30],[-.98,1.19],[-.73,1.18]]
        if quarter_recipe is None:
            profile_solid('rear_quarter_panel',body,catmull(rearprof,4,True),side,half,.025,0)
        else:
            qv,qf,iv,iff=quarter_surface(catmull(rearprof,4,True).tolist(),side,half,.025,quarter_recipe,earclip)
            geometry('rear_quarter_panel',body,qv,qf,0)
            geometry('rear_quarter_recessed_surface',body,iv,iff,6)
        rt=[[side*(half+.028),y,z]for z,y in catmull(rearprof,4,True)];rt.append(rt[0]);tube('rear_quarter_fine_lining',body,rt,.0025,3,6)
        for z,y in [(.36,1.10),(-.43,1.15),(-.43,.87)]:
            box('small_door_hardware',body,(side*(width(y)+.066),y,z),(.016,.015,.045),3)
        # Prospective source-footplate refinement: the visible plate has two
        # separated small treads. Exact metres/hidden/opposite construction are
        # reconstructed. Preserve existing support endpoints and outerX; reconstructed
        #20mm producer-thickness encloses each actual support end cap.
        # One owned part per side still; no support/door/body/pivot amendment.
        step_vertices=[];step_faces=[];step_sides=12
        for step_z in [-.20,.07]:
            step_base=len(step_vertices)
            for step_y in [.34,.36]:
                step_vertices.extend([[side*.72+.14*math.cos(step_i*math.tau/step_sides),
                                       step_y,step_z+.065*math.sin(step_i*math.tau/step_sides)]
                                      for step_i in range(step_sides)])
            step_faces.extend([[step_base+step_i for step_i in range(step_sides)],
                               [step_base+step_sides+step_i for step_i in reversed(range(step_sides))]])
            step_faces.extend([[step_base+step_i,step_base+step_sides+step_i,
                                step_base+step_sides+(step_i+1)%step_sides,
                                step_base+(step_i+1)%step_sides]
                               for step_i in range(step_sides)])
        geometry('door_step',body,step_vertices,step_faces,4)
        # V15 source proposal: slender curved/drop stems replace the visible
        # heavy straight diagonals. Near-side silhouette is plate-guided;
        #16x8mm section, hidden route and opposite mirror are reconstruction.
        # Retain V14 pad geometry and exact original attachment centers.
        for z in [-.20,.07]:
            support_curve=catmull([[.45,.65],[.43,.57],[.435,.49],
                                   [.47,.43],[.565,.3975],[.685,.385],[.72,.35]],3)
            support_vertices=[];support_count=len(support_curve)
            for support_i,support_xy in enumerate(support_curve):
                support_u=(support_curve[min(support_i+1,support_count-1)]-
                           support_curve[max(support_i-1,0)])
                support_u/=np.linalg.norm(support_u)
                support_v=np.array([0.,0.,.008])
                support_q=np.array([support_u[1],-side*support_u[0],0.])*.004
                support_center=np.array([side*support_xy[0],support_xy[1],z])
                support_vertices.extend([support_center+support_a*support_v+support_b*support_q
                                         for support_a,support_b in [(-1,-1),(1,-1),(1,1),(-1,1)]])
            support_faces=[[3,2,1,0],list(range(4*(support_count-1),4*support_count))]
            support_faces.extend([[4*support_i+support_j,4*support_i+(support_j+1)%4,
                                   4*(support_i+1)+(support_j+1)%4,4*(support_i+1)+support_j]
                                  for support_i in range(support_count-1) for support_j in range(4)])
            geometry('step_support',body,support_vertices,support_faces,4)

    # Front and rear cabin surfaces and original empty interior.
    # V13: close on the existing inner shell, including width()'s1.26m breakpoint.
    # Same Y/Z envelope, material and part; three rows avoid a tiny open join.
    wrap_vertices,wrap_faces,wrap_normals=coach_front_wrap(lower,width,rows=lod_n(28,'body_rows'),
                                             columns=lod_n(20,'body_columns'))
    geometry('cabin_front_lower',body,wrap_vertices,wrap_faces,0,normals_override=wrap_normals)
    box('front_glass',body,(0,1.55,.255),(1.12,.46,.009),cabin_glass)
    geometry('front_sill_connector',body,[[-half,1.27,.43],[half,1.27,.43],[half,1.34,.27],[-half,1.34,.27]],[[0,1,2,3]],0)
    for x in [-half,0,half]:beam('front_window_stile',body,(x,1.31,.27),(x,1.81,.27),.022,1)
    for y in [1.31,1.81]:beam('front_window_rail',body,(-half,y,.27),(half,y,.27),.025,1)
    # Convex rear bulkhead instead of C02's flat rectangular rear box.
    v=[];ny=lod_n(14,'rear_rows');nx=lod_n(20,'rear_columns')
    for iy in range(ny+1):
        y=1.03+(1.73-1.03)*iy/ny
        for ix in range(nx+1):
            x=-half+2*half*ix/nx;z=-1.045-.07*(1-(x/half)**2)*math.sin(math.pi*(y-1.03)/.70)
            v.append([x,y,z])
    ff=[]
    for iy in range(ny):
        for ix in range(nx):i=iy*(nx+1)+ix;ff.append([i,i+1,i+nx+2,i+nx+1])
    # Rear surface normal faces -Z.
    geometry('rounded_rear_bulkhead',body,v,[list(reversed(f))for f in ff],0,smooth=True)
    # V13: retain the floor, but keep its entire thickness inside the SAME side profile.
    #3mm is an original engineering inset, not a catalogue measurement. Coordinates
    #are producer-frame; geometry() applies the existing bodyY affine exactly once.
    floor_y0,floor_y1=.75,.79
    floor_levels=sorted(set([floor_y0,floor_y1]+[y for z,y in lower if floor_y0<y<floor_y1]))
    def floor_span(y):
        crossings=sorted(z0+(z1-z0)*(y-y0)/(y1-y0)
                         for (z0,y0),(z1,y1) in zip(lower,lower[1:]+lower[:1])
                         if (y0<=y<y1) or (y1<=y<y0))
        if len(crossings)!=2:raise ValueError('Floor needs one unambiguous body-profile interval')
        return crossings
    floor_spans=[floor_span(y) for y in floor_levels]
    floor_z0=max(-.595,max(span[0] for span in floor_spans)+.003)
    floor_z1=min(.355,min(span[1] for span in floor_spans)-.003)
    floor_half=min(width(y) for y in floor_levels)-.003
    if not(floor_z1>floor_z0 and floor_half>0):raise ValueError('Empty inset floor section')
    box('interior_floor',body,(0,.77,(floor_z0+floor_z1)/2),(2*floor_half,.04,floor_z1-floor_z0),1)
    box('passenger_bench_base',body,(0,.94,-.72),(1.01,.22,.36),1)
    # T-3084: original soft pads stay inside the old seat boxes. The occupied
    # lithograph supplies no hidden upholstery pattern; do not invent tufting.
    for name,center,size,axis in [('passenger_cushion',(0,1.08,-.72),(1.00,.08,.36),1),
                                  ('passenger_back',(0,1.28,-.94),(.99,.37,.045),2)]:
        pad_vertices,pad_faces=rounded_pad(center,size,axis=axis,
                                         samples=lod_n(32,'cushion_sections'))
        geometry(name,body,pad_vertices,pad_faces,2,smooth=True)
    # Longitudinally shaped closed roof and a softly crowned cross section.
    roof=catmull(p['roof_longitudinal_profile_z_y_m'],lod_n(5,'roof_longitudinal_steps'));nx=lod_n(20,'roof_cross_steps');v=[]
    roof_thickness=p['roof_sheet_thickness_m']
    for z,edge_y in roof:
        for ix in range(nx+1):x=-.64+1.28*ix/nx;y=edge_y+p['roof_cross_crown_m']*(1-(x/.64)**2);v.append([x,y,z])
    ff=[]
    for iz in range(len(roof)-1):
        for ix in range(nx):i=iz*(nx+1)+ix;ff.append([i,i+1,i+nx+2,i+nx+1])
    geometry('swept_crowned_roof',body,v,[list(reversed(f))for f in ff],0,smooth=True)
    geometry('roof_underside',body,[[x,y-roof_thickness,z]for x,y,z in v],ff,0,smooth=True)
    # Close the physical roof edge rather than leaving a one-sided floating sheet.
    boundary=list(range(nx+1))+[i*(nx+1)+nx for i in range(1,len(roof))]+list(range((len(roof)-1)*(nx+1)+nx-1,(len(roof)-1)*(nx+1)-1,-1))+[i*(nx+1)for i in range(len(roof)-2,0,-1)]
    roofedge=[]
    for i,j in zip(boundary,boundary[1:]+boundary[:1]):
        roofedge.append([v[i],[v[i][0],v[i][1]-roof_thickness,v[i][2]],[v[j][0],v[j][1]-roof_thickness,v[j][2]],v[j]])
    for quad in roofedge:geometry('roof_edge_fascia',body,quad,[[3,2,1,0]],1)
    for side in [-1,1]:
        tube('roof_drip_edge',body,[[side*.64,y,z]for z,y in roof],p['roof_drip_edge_radius_m'],1,8)
        headprof=[[.33,1.78],[.22,1.76],[.07,1.80],[-.12,1.78],[-.35,1.72],[-1.10,1.68]]+[[z,y-.018]for z,y in p['roof_longitudinal_profile_z_y_m']]
        profile_solid('closed_upper_side_header',body,headprof,side,half-.01,.04,0)
    for z,y in [roof[0],roof[-1]]:tube('roof_end_lip',body,[[x,y+p['roof_cross_crown_m']*(1-(x/.64)**2),z]for x in np.linspace(-.64,.64,lod_n(20,'roof_cross_steps')+1)],p['roof_end_lip_radius_m'],1,8)
    for z,edge_y,bottom in [(.28,float(np.interp(.28,roof[:,0],roof[:,1])),1.79),(-1.065,float(roof[0,1]),1.70)]:
        xx=np.linspace(-half,half,lod_n(20,'roof_cross_steps')+1);upper=[[x,edge_y+p['roof_cross_crown_m']*(1-(x/.64)**2)-.025,z]for x in xx]
        lower=[[x,bottom,z]for x in xx]
        hf=[[i,i+1,len(xx)+i+1,len(xx)+i]for i in range(len(xx)-1)]
        geometry('closed_end_crown_header',body,lower+upper,hf if z>0 else[list(reversed(f))for f in hf],0)

    # Empty elevated driver seat; source coachmen do not attest hidden upholstery.
    sy,sz=p['driver_bench_center_y_z_m'];sw=p['driver_bench_width_m'];sd=p['driver_bench_depth_m']
    box('driver_perch_base',body,(0,sy-.07,sz),(sw,.09,sd),1)
    # Rounded capsule-like cushion loft, original unoccupied reconstruction.
    section=[];n=lod_n(40,'cushion_sections')
    for i in range(n):
        t=math.tau*i/n;section.append([math.copysign(abs(math.cos(t))**.28,math.cos(t))*sw/2,math.copysign(abs(math.sin(t))**.28,math.sin(t))*sd/2])
    vv=[]
    for yy,scale in [(sy-.015,.94),(sy+.020,1),(sy+.055,.94)]:
        for x,z in section:vv.append([x*scale,yy,sz+z*scale])
    fs=[list(range(n-1,-1,-1)),list(range(2*n,3*n))]
    for j in range(2):
        for i in range(n):k=(i+1)%n;fs.append([j*n+i,j*n+k,(j+1)*n+k,(j+1)*n+i])
    geometry('rounded_empty_driver_cushion',body,vv,[list(reversed(f))for f in fs],2,smooth=True)
    # A restrained sewn edge, not a source-attested upholstery design. It sits
    # within the previous cushion envelope; the seat reference does not move.
    seam=[[x*.91,sy+.045,sz+z*.91]for x,z in section]
    seam.append(seam[0]);tube('driver_cushion_edge_piping',body,seam,.0025,2,6)
    box('driver_backboard',body,(0,sy+.14,sz-.19),(sw,.25,.035),1)
    fy,fz=p['driver_footboard_y_z_m'];box('driver_footboard',body,(0,fy,fz),(1.04,.035,.36),1)
    for side in [-1,1]:
        beam('perch_support',body,(side*.43,.78,.65),(side*.43,sy-.10,sz),.040,4)
        tube('driver_side_rail',body,[[side*.53,sy+.03,sz+.17],[side*.53,sy+.16,sz+.12],[side*.53,sy+.19,sz-.18]],.015,1,8)
        beam('footboard_support',body,(side*.43,.78,.60),(side*.43,fy-.02,fz+.10),.024,4)

    # V18 SOURCE-ONLY proposal: plate0095 has a rounded coach-lamp head,
    # oval bright-rimmed faces and a narrower lower body. Exact metric shape,
    # glazing construction, hidden faces and opposite-side mirror are reconstructed.
    # No source pixels, new material, illumination, shared finish or motion change.
    # The original arm and centres remain exact. All dimensions below are producer
    # metres before the existing body_vertical_affine, not historic measurements.
    lamp_head_profile=[(-.040,.015),(.040,.015),(.05768,.02232),
                       (.065,.040),(.065,.135),(.05768,.15268),
                       (.040,.160),(-.040,.160),(-.05768,.15268),
                       (-.065,.135),(-.065,.040),(-.05768,.02232)]
    lamp_n=len(lamp_head_profile) # 12; convex rounded rectangle in (Z,Y).
    def lamp_aperture(name,outer,center,radii,point,normal_sign):
        # Radial correspondence from the convex outer polygon to a strict inner
        # ellipse. The hole is physical; no opaque full panel backs its glazing.
        # point(u,v,depth) maps the local face into the existing lamp carrier.
        inner=[]
        for u,v in outer:
            du,dv=u-center[0],v-center[1]
            scale=1/math.sqrt((du/radii[0])**2+(dv/radii[1])**2)
            inner.append((center[0]+du*scale,center[1]+dv*scale))
        n=len(outer)
        vertices=[point(u,v,0.) for u,v in outer+inner]
        faces=[[i,(i+1)%n,n+(i+1)%n,n+i]for i in range(n)]
        if normal_sign<0:faces=[list(reversed(f))for f in faces]
        geometry(name+'_bright_surround',body,vertices,faces,3)
        # One-millimetre reveal meets the recessed glass perimeter. This closes
        # the actual aperture rather than leaving an overlaid decorative disk.
        vertices=[point(u,v,d)for d in [0.,-.001]for u,v in inner]
        faces=[[i,(i+1)%n,n+(i+1)%n,n+i]for i in range(n)]
        if normal_sign<0:faces=[list(reversed(f))for f in faces]
        geometry(name+'_reveal',body,vertices,faces,4)
        face=list(range(n))
        if normal_sign<0:face.reverse()
        geometry(name+'_glass',body,[point(u,v,-.001)for u,v in inner],[face],5)
    for side in [-1,1]:
        cx=side*.60;cy=1.53;cz=.44
        beam('lamp_arm',body,(side*.49,1.30,.40),(cx,cy-.12,cz),.018,4)
        # Closed upper shell. Its front rectangle and outward side contain the
        # two apertures below; the hidden inward side is a declared plain back.
        v=[[cx+x,cy+y,cz+z]for x in [-.065,.065]for z,y in lamp_head_profile]
        faces=[[i,lamp_n+i,lamp_n+(i+1)%lamp_n,(i+1)%lamp_n]
               for i in range(lamp_n)if i!=3] # front straight wall is an aperture.
        geometry('lamp_rounded_upper_shell',body,v,faces,4)
        back=[lamp_n+i for i in range(lamp_n)]if side<0 else list(range(lamp_n))
        if side<0:back.reverse()
        geometry('lamp_hidden_inner_back',body,v,[back],4)
        # (Z,Y) counterclockwise has -X normal; outward face is mirrored only
        # as explicit reconstruction, with the same current lamp centres.
        lamp_aperture('lamp_outward_oval',lamp_head_profile,(0.,.0875),(.044,.054),
                      lambda z,y,d:(cx+side*(.065+d),cy+y,cz+z),-side)
        # (X,Y) counterclockwise has +Z normal. All 12 outer points are on the
        # existing front-wall rectangle, including its four exact corners.
        hx=.065;hy=.0475;my=.0875
        front=[(-hx,my-hy),(-hx/3,my-hy),(hx/3,my-hy),(hx,my-hy),
               (hx,my-hy/3),(hx,my+hy/3),(hx,my+hy),(hx/3,my+hy),
               (-hx/3,my+hy),(-hx,my+hy),(-hx,my+hy/3),(-hx,my-hy/3)]
        lamp_aperture('lamp_forward_oval',front,(0.,my),(.043,.036),
                      lambda x,y,d:(cx+x,cy+y,cz+.065+d),1)
        # Narrow lower framed body; existing glass/iron choices are retained as
        # reconstructions. The bottom cap meets the original arm endpoint.
        v=[[cx+x,cy+y,cz+z]for y in [-.12,.015]
           for x,z in [(-.028,-.028),(.028,-.028),(.028,.028),(-.028,.028)]]
        geometry('lamp_narrow_lower_glass',body,v,
                 [[i,4+i,4+(i+1)%4,(i+1)%4]for i in range(4)],5)
        for x,z in [(-.028,-.028),(.028,-.028),(.028,.028),(-.028,.028)]:
            # Closed triangular-section 6mm stiles preserve the coarse-mid lamp
            # triangle budget; their hidden cross section is reconstructed.
            v=[[cx+x+.003*math.cos(i*math.tau/3),cy+y,
                cz+z+.003*math.sin(i*math.tau/3)]
               for y in [-.12,.015]for i in range(3)]
            faces=[[0,1,2],[5,4,3]]+[[i,3+i,3+(i+1)%3,(i+1)%3]for i in range(3)]
            geometry('lamp_lower_corner_stile',body,v,faces,4)
        box('lamp_lower_base',body,(cx,cy-.116,cz),(.062,.008,.062),4)
        # Same finial radius/end height, now seated directly on the rounded head.
        tube('lamp_finial',body,[[cx,cy+.160,cz],[cx,cy+.197,cz]],.009,3,8)

    rear=node('vehicle_running_gear_rear',root,(0,RR,-WB/2));front=node('vehicle_steer_front',root,(0,RF,WB/2))
    for frame in [rear,front]:box('black_axle',frame,(0,0,0),(TRACK+.12,.045,.045),4)
    beam('longitudinal_reach',root,(0,.44,-WB/2),(0,.44,WB/2),.055,4)
    for z,r in [(-WB/2,RR),(WB/2,RF)]:
        for x in [-.39,.39]:
            for layer in range(4):
                extent=.34-layer*.045
                path=[[x,r+.065+layer*.010+.105*(q/.34)**2,z+q]for q in np.linspace(-extent,extent,lod_n(11,'spring_steps'))]
                for q1,q2 in zip(path,path[1:]):beam('leaf_spring',root,q1,q2,.017,4,depth=.006)
            for q in [-.34,.34]:beam('spring_hanger',root,(x,r+.18,z+q),(x,.80,z+q),.018,4)
    for frame,r,label in [(rear,RR,'rear'),(front,RF,'front')]:
        for side,side_name in [(-1,'right'),(1,'left')]:
            wheel=node('vehicle_wheel_'+label+'_'+side_name,frame,(side*TRACK/2,0,0))
            circle_tube('rounded_iron_tire',wheel,r-.004,.041,.004,4)
            circle_tube('slender_painted_felloe',wheel,r-.021,.038,.016,1)
            circle_tube('rounded_hub',wheel,.049,.128,.017,1,40)
            solid_axial_body('solid_painted_hub_core',wheel,p['hub_core_profile_axial_radial_m'],1,p['hub_core_segments'])
            spoke_sides=lod_n(8,'spoke_cross_sides')
            for i in range(p['spokes_per_wheel']):
                t=i*math.tau/p['spokes_per_wheel'];direction=np.array([0,math.cos(t),math.sin(t)]);tangent=np.array([0,-math.sin(t),math.cos(t)])
                vv=[]
                for distance,wid,axial in [(.060,.025,.028),(r-.035,.014,.018)]:
                    c=direction*distance
                    for k in range(spoke_sides):phi=k*math.tau/spoke_sides;vv.append(c+np.array([axial/2*math.cos(phi),0,0])+tangent*wid/2*math.sin(phi))
                ff=[list(range(spoke_sides-1,-1,-1)),list(range(spoke_sides,2*spoke_sides))]+[[k,(k+1)%spoke_sides,(k+1)%spoke_sides+spoke_sides,k+spoke_sides]for k in range(spoke_sides)]
                geometry('tapered_rounded_spoke',wheel,vv,ff,1,smooth=True)
            cap=node('hubcap',wheel,(side*.079,0,0));circle_tube('bright_hubcap_rim',cap,.037,.020,.009,3,40)
            solid_axial_body('solid_bright_hub_button',cap,p['hub_button_profile_axial_radial_m'],3,p['hub_button_segments'],side)
            # Original functional support frames are retained as named geometry,
            # but the specimen is static and no steering/motion is accepted.
            if label=='rear':
                arc=np.linspace(.10,math.pi-.10,lod_n(44,'mudguard_steps'));rr=r+.040;v=[]
                for xx in [side*TRACK/2-.052,side*TRACK/2+.052]:
                    for aa in arc:v.append([xx,r+rr*math.sin(aa),-WB/2+rr*math.cos(aa)])
                n=len(arc);geometry('thin_rear_mudguard',root,v,[[i,i+1,n+i+1,n+i]for i in range(n-1)],0,smooth=True)

    # Paired-team central pole, deliberately parked down; no single-horse shafts.
    pole=node('vehicle_team_pole',root);start=np.array([0,RF+.025,WB/2]);end=np.array([0,p['pole_parked_tip_y_m'],WB/2+p['pole_length_m']])
    beam('central_team_pole_parked',pole,start,end,.055,1)
    # Small explicit ground shoe under pole tip, original reconstructed hardware.
    box('parked_pole_ground_shoe',pole,(0,.017,end[2]-.025),(.065,.034,.10),4)
    box('team_pole_yoke_bracket',pole,(0,RF+.025,WB/2+.22),(.23,.055,.06),4)
    node('vehicle_hitch_team',pole,end)
    # Additive plate-observed near-side details; all pre-existing parts stay exact.
    # Hidden attachment depth is inferred. No opposite-side or step-count claim.
    for detail in feature_plan(p):
        if detail['kind']=='tube':
            tube(detail['name'],body,detail['path'],detail['radius_m'],detail['material'],detail['sides'])
        elif detail['kind']=='beam':
            beam(detail['name'],body,detail['start'],detail['end'],detail['width_m'],detail['material'])
        else:raise ValueError('Unknown proposed detail primitive')
    node('vehicle_seat_driver',body,(0,sy+.065,sz))
    node('vehicle_seat_passenger_01',body,(.23,1.13,-.72));node('vehicle_seat_passenger_02',body,(-.23,1.13,-.72))
    # No occupant, door, board or driving animations are supplied.
    materials=[
        {'name':'deep_green_painted_body','pbrMetallicRoughness':{'baseColorFactor':[.020,.038,.029,1],'metallicFactor':0,'roughnessFactor':.29},'extensions':{'KHR_materials_clearcoat':{'clearcoatFactor':.28,'clearcoatRoughnessFactor':.20}}},
        {'name':'black_painted_timber','pbrMetallicRoughness':{'baseColorFactor':[.016,.019,.018,1],'metallicFactor':0,'roughnessFactor':.35}},
        {'name':'reconstructed_brown_leather','pbrMetallicRoughness':{'baseColorFactor':[.082,.029,.014,1],'metallicFactor':0,'roughnessFactor':.67}},
        {'name':'unmeasured_bright_trim','pbrMetallicRoughness':{'baseColorFactor':[.40,.42,.37,1],'metallicFactor':.85,'roughnessFactor':.25}},
        {'name':'blackened_iron','pbrMetallicRoughness':{'baseColorFactor':[.023,.026,.025,1],'metallicFactor':.85,'roughnessFactor':.40}},
        {'name':'reconstructed_clear_glass','pbrMetallicRoughness':{'baseColorFactor':[.38,.49,.50,.25],'metallicFactor':0,'roughnessFactor':.10},'alphaMode':'BLEND'},
    ]
    if quarter_recipe is not None:materials.append(quarter_recipe['material'])
    if p.get('photo_finish_v19'):
        materials=finished_materials(materials,p['photo_finish_v19'])
    binary=bytearray();views=[];access=[];meshes=[]
    def append(arr,kind):
        arr=np.asarray(arr,dtype='<f4');off=len(binary);binary.extend(arr.tobytes());vi=len(views);views.append({'buffer':0,'byteOffset':off,'byteLength':arr.nbytes,'target':34962});ai=len(access);access.append({'bufferView':vi,'componentType':5126,'count':len(arr),'type':kind,'min':arr.min(axis=0).tolist(),'max':arr.max(axis=0).tolist()});return ai
    for (parent,mat),b in batches.items():
        positions=np.asarray(b['positions'],dtype='<f4');normals=np.asarray(b['normals'],dtype='<f4')
        if not(np.isfinite(positions).all()and np.isfinite(normals).all()):raise ValueError('Non-finite original geometry')
        ai=append(positions,'VEC3');ni=append(normals,'VEC3');mi=len(meshes);meshes.append({'name':'surface_'+nodes[parent]['name']+'_'+str(mat),'primitives':[{'attributes':{'POSITION':ai,'NORMAL':ni},'material':mat}]});n=node(meshes[-1]['name'],parent);nodes[n]['mesh']=mi
    extra={'asset_id':p['asset_id'],'license':'GPL-3.0-or-later','units':'m','up_axis':'+Y','forward_axis':'+Z','root_datum':'ground midpoint between axles','source_id':p['source_id'],'source_reference':{'scan_leaf':p['reference_scan_leaf'],'sha256':p['reference_sha256'],'actually_viewed':True,'usage':'Appearance-guided original geometry with manually estimated source landmarks; no image pixels embedded as textures','claim':'Catalogmaker/type1893; specific1904specimen/owner/placement reconstructed'},'scene_year':1904,'confidence':'reconstructed','status':'Original1893StudebakerBrougham appearance reconstruction; static empty closed specimen; photographic acceptance pending actual source comparison','dimensions_tier':p['dimension_tier'],'parameters':p,'statistics':{'triangles':sum(len(b['positions'])//3 for b in batches.values()),'meshes':len(meshes),'nodes':len(nodes)},'parts':parts,'door_interaction_enabled':False,'boarding_enabled':False,'traffic_enabled':False,'occupants':False,'liberties':p['limits']}
    nodes=[{k:v for k,v in n.items()if k!='children'or v}for n in nodes]
    doc={'asset':{'version':'2.0','generator':'Chicago4D original StudebakerBrougham source reconstruction'},'scene':0,'scenes':[{'nodes':[root]}],'nodes':nodes,'meshes':meshes,'materials':materials,'bufferViews':views,'accessors':access,'buffers':[{'byteLength':len(binary)}],'extensionsUsed':['KHR_materials_clearcoat','KHR_materials_transmission','KHR_materials_ior'],'extras':extra}
    if quarter_recipe is not None:
        doc['extras']['rear_quarter_study']={'recipe_sha256':hashlib.sha256(a.rear_quarter_recipe.read_bytes()).hexdigest(),'interpretation':quarter_recipe['interpretation'],'appearance_accepted':False}
    j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4);binary+=b'\0'*((-len(binary))%4)
    out=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
    a.output.mkdir(parents=True);(a.output/'brougham.glb').write_bytes(out);(a.output/'brougham.json').write_text(json.dumps(extra,indent=2)+'\n');print(json.dumps({'sha256':hashlib.sha256(out).hexdigest(),'bytes':len(out),'stats':extra['statistics']}))


if __name__=='__main__':main()
