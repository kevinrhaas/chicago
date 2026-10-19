# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure prepared-source sole LBS check at dense and 30fps-key sampling. No bpy."""
from __future__ import annotations
import math
from human_grounded_gait import pose_at_phase, prepare_legs, CYCLE_FRAMES, SPEED_M_S, CYCLE_DURATION_S

def eye(): return [[float(i==j) for j in range(4)] for i in range(4)]
def mm(a,b): return [[sum(a[i][k]*b[k][j]for k in range(4))for j in range(4)]for i in range(4)]
def pivot(h,a):
    c,s=math.cos(a),math.sin(a);m=eye();m[1][1]=m[2][2]=c;m[1][2]=-s;m[2][1]=s
    for i in range(3):m[i][3]=h[i]-sum(m[i][j]*h[j]for j in range(3))
    return m

def transform(m,p):return [sum(m[i][j]*p[j]for j in range(3))+m[i][3]for i in range(3)]
def skin(p,w,D):return [sum(v*transform(D[b],p)[i]for b,v in w.items())for i in range(3)]

def soles(body,bones,shoe_offset=.005,scale=1.0):
    out={}
    for side in ('l','r'):
        points=[p for m in body['meshes']for p,w in zip(m['positions_m'],m['weights'])if sum(v for b,v in w.items()if b in('foot_'+side,'ball_'+side))>.35 and p[1]<.16]
        if not points:raise ValueError('no actual source foot bounds')
        xmin,xmax=min(p[0]for p in points),max(p[0]for p in points);zmin,zmax=min(p[2]for p in points),max(p[2]for p in points);cx,cz=(xmin+xmax)/2,(zmin+zmax)/2;rx,rz=(xmax-xmin)/2+shoe_offset/scale,(zmax-zmin)/2+shoe_offset/scale
        vertices=[]
        for k in range(20):
            a=2*math.pi*k/20;z=cz+rz*math.sin(a);blend=max(0,min(1,(z-bones['ball_'+side]['head_m'][2]+.04)/.08));vertices.append(([v*scale for v in (cx+rx*math.cos(a),0,z)],{'foot_'+side:1-blend,'ball_'+side:blend}))
        vertices.append(([cx*scale,0,cz*scale],{'foot_'+side:1.0}));out[side]=vertices
    return out

def sampled_pose(legs,phase,keys=None):
    if keys is None:return pose_at_phase(legs,phase)
    # All lower-limb channels are rotations around fixed local conjugates of X.
    # Shortest-path quaternion SLERP thus equals linear interpolation of these angles.
    j=min(CYCLE_FRAMES-1,int(phase*CYCLE_FRAMES));w=phase*CYCLE_FRAMES-j;a,b=keys[j],keys[j+1]
    angles={}
    for name in a['x_rotations_rad']:
        av,bv=a['x_rotations_rad'][name],b['x_rotations_rad'][name]
        if abs(av-bv)>=math.pi:raise ValueError('angle interpolation no longer equivalent to shortest SLERP')
        angles[name]=av+(bv-av)*w
    return dict(pelvis_delta_m=tuple(x+(y-x)*w for x,y in zip(a['pelvis_delta_m'],b['pelvis_delta_m'])),x_rotations_rad=angles)

def measure(body,mode='dense',shoe_offset=.005,scale=1.0):
    bones={b['name']:b for b in body['skeleton']};legs=prepare_legs(bones,scale);foot=soles(body,bones,shoe_offset,scale);keys=[pose_at_phase(legs,i/CYCLE_FRAMES)for i in range(CYCLE_FRAMES+1)]if mode=='keys30fps_slerp'else None
    if mode not in ('dense','keys30fps_slerp'):raise ValueError(mode)
    planted={};maxdrift=0;maxheight=0;low=math.inf;supportgap=0;ankleerror=0;first=None;last=None;kneemin=math.inf
    for i in range(1001):
        phase=i/1000;pose=sampled_pose(legs,phase,keys);contact=pose_at_phase(legs,phase);pel=eye()
        for q in range(3):pel[q][3]=pose['pelvis_delta_m'][q]
        allpoints={};support=0
        for side,offset in (('l',0),('r',.5)):
            leg=legs[side];angles=pose['x_rotations_rad'];thigh=mm(pel,pivot(leg['hip'],angles['thigh_'+side]));calf=mm(thigh,pivot(leg['knee'],angles['calf_'+side]));Dfoot=mm(calf,pivot(leg['ankle'],angles['foot_'+side]));D={'foot_'+side:Dfoot,'ball_'+side:Dfoot};points=[skin(p,w,D)for p,w in foot[side]];world=[[p[0],p[1],p[2]+SPEED_M_S*CYCLE_DURATION_S*phase]for p in points];allpoints[side]=points;low=min(low,min(p[1]for p in points));ankleerror=max(ankleerror,math.dist(transform(Dfoot,leg['ankle']),contact['legs'][side]['ankle_target_m']))
            if contact['legs'][side]['support']:
                support+=1;maxheight=max(maxheight,max(abs(p[1])for p in points));group=(side,math.floor(phase+offset));old=planted.setdefault(group,world);maxdrift=max(maxdrift,max(math.dist(a,b)for a,b in zip(old,world)))
            hip=[leg['hip'][q]+pose['pelvis_delta_m'][q]for q in range(3)];knee=transform(thigh,leg['knee']);ankle=transform(Dfoot,leg['ankle']);vec=[ankle[q]-hip[q]for q in range(3)];t=sum((knee[q]-hip[q])*vec[q]for q in range(3))/sum(x*x for x in vec);kneemin=min(kneemin,knee[2]-(hip[2]+t*vec[2]))
        supportgap+=not support
        if first is None:first=allpoints
        last=allpoints
    closure=max(math.dist(a,b)for s in ('l','r')for a,b in zip(first[s],last[s]));return dict(mode=mode,samples=1001,authored_keys=37 if keys else 1001,max_planted_sole_world_drift_m=maxdrift,max_supported_sole_height_error_m=maxheight,minimum_sole_height_m=low,phases_without_support=supportgap,max_ankle_target_residual_m=ankleerror,minimum_forward_knee_pole_m=kneemin,sole_loop_closure_m=closure,no_scale_or_stretch=True,not_measured=['actual Blender fcurves','exported GLB skin','clothing fit','photographic/biological gait quality'])
