# SPDX-License-Identifier: GPL-3.0-or-later
"""Original manually landmark-guided fittings; hidden construction reconstructed.

No image pixels are embedded. This module plans additive near-side detail only;
no lock mechanism, heraldry, opposite-side duplicate or new step is attested.
"""
import math


def sample_open(points, steps):
    out=[]
    for i in range(len(points)-1):
        a,b,c,d=points[max(0,i-1)],points[i],points[i+1],points[min(len(points)-1,i+2)]
        for k in range(steps):
            t=k/steps
            out.append([.5*(2*b[j]+(-a[j]+c[j])*t+(2*a[j]-5*b[j]+4*c[j]-d[j])*t*t+(-a[j]+3*b[j]-3*c[j]+d[j])*t*t*t) for j in range(2)])
    return out+[list(points[-1])]


def feature_plan(p):
    detail=p['source_detail_v11'];side=detail['observed_side_x_sign']
    if side!=1:raise ValueError('Only the actually observed positive-X side is proposed')
    half=p['body_half_width_m']
    width=lambda y:half-.18*max(0,min(1,(1.26-y)/.91))
    f=[]
    def tube(name,path,r):
        if not math.isfinite(r) or r<=0:raise ValueError('Invalid detail radius')
        f.append({'kind':'tube','name':name,'path':path,'radius_m':r,'material':3,'sides':8})
    def pin(name,y,z):
        # Small attachment depth/section is engineering reconstruction, not source evidence.
        f.append({'kind':'beam','name':name,'start':[width(y)+.050,y,z],
                  'end':[width(y)+.060,y,z],'width_m':.010,'material':3})
    latch=detail['forward_oval_latch'];y,z=latch['center_producer_y_z_m'];ry,rz=latch['radii_producer_y_z_m'];n=latch['ring_samples']
    path=[]
    for k in range(n):
        a=math.tau*k/n;yy=y+ry*math.sin(a);zz=z+rz*math.cos(a)
        path.append([width(yy)+.060,yy,zz])
    path.append(path[0]);tube('source_near_forward_oval_latch',path,latch['tube_radius_m'])
    for zz in [z-rz,z+rz]:pin('source_near_latch_attachment_inferred',y,zz)
    fitting=detail['central_pronged_fitting'];y,z=fitting['center_producer_y_z_m']
    cup=sample_open(fitting['cup_offsets_z_y_m'],6)
    tube('source_near_central_open_fitting',[[width(y+dy)+.060,y+dy,z+dz] for dz,dy in cup],fitting['tube_radius_m'])
    for dz in [-.035,0,.035]:
        lean=0 if dz==0 else math.copysign(.006,dz)
        local=[[dz,-.016],[dz,.015],[dz+lean,.034]]
        tube('source_near_central_fitting_prong',[[width(y+dy)+.060,y+dy,z+zz] for zz,dy in local],.0030)
    for dz in [-.038,.038]:pin('source_near_fitting_attachment_inferred',y-.020,z+dz)
    for item in f:
        values=item.get('path',[item.get('start'),item.get('end')])
        if not all(math.isfinite(x) for v in values for x in v):raise ValueError('Nonfinite detail witness')
    return f
