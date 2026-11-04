"""Exact event predicates and conservative locus bounds for an EXTERNAL mode.

This module neither loads an application asset nor grants source authority.
Production orchestration must bind source/side/face ledgers before calling it.
No ray distance is discarded by a geometric epsilon. Old modes are untouched.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
import math
import numpy as np

BODY_LIMIT=Q(14,1000)
CONTACT_LIMIT=Q(7,1000)
PREDICATE_TOLERANCE_M=1e-9  # detector contract; not a padded containment volume
CELL_HALF_ARC_M=2.5e-5
ARITHMETIC_RESERVE_M=1e-9  # added to an upper bound, never subtracted from a limit
RAYS=((1000,317,193),(-231,1000,419),(273,-391,1000),(619,173,-997),(-853,997,229),(431,-887,997))

class Rejected(ValueError):
    def __init__(self,code,detail=''):
        self.code=code
        super().__init__(code+(': '+str(detail)if detail else''))

def need(ok,code,detail=''):
    if not ok:raise Rejected(code,detail)

def exact(v):
    return tuple(x if isinstance(x,Q)else Q.from_float(float(x))for x in v)

def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def mul(a,t):return tuple(x*t for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

def scalar_bounds(q):
    f=float(q);need(math.isfinite(f),'nonfinite_exact_conversion')
    r=Q.from_float(f)
    return (np.nextafter(f,-np.inf)if r>q else f,np.nextafter(f,np.inf)if r<q else f)

def bounds(points):
    pairs=np.asarray([[scalar_bounds(x)for x in p]for p in points],dtype=float)
    return pairs[:,:,0],pairs[:,:,1]

def iadd(a,b):return np.nextafter(a[0]+b[0],-np.inf),np.nextafter(a[1]+b[1],np.inf)
def isub(a,b):return np.nextafter(a[0]-b[1],-np.inf),np.nextafter(a[1]-b[0],np.inf)
def imul(a,b):
    p=np.stack([a[0]*b[0],a[0]*b[1],a[1]*b[0],a[1]*b[1]])
    return np.nextafter(p.min(axis=0),-np.inf),np.nextafter(p.max(axis=0),np.inf)

def norm_upper(a):
    maximum=np.maximum(np.abs(a[0]),np.abs(a[1]))
    squares=np.nextafter(maximum*maximum,np.inf)
    total=np.zeros(squares.shape[:-1])
    for k in range(3):total=np.nextafter(total+squares[...,k],np.inf)
    return np.nextafter(np.sqrt(total),np.inf)

@dataclass(frozen=True)
class Segment:
    a:tuple
    b:tuple
    def __post_init__(self):
        object.__setattr__(self,'a',exact(self.a));object.__setattr__(self,'b',exact(self.b))
        need(self.a!=self.b,'zero_length_locus')
    def point(self,t):return add(self.a,mul(sub(self.b,self.a),t))
    def floats(self):return np.asarray([[float(x)for x in self.a],[float(x)for x in self.b]])
    def data(self):return self.floats().tolist()

def on_triangle(p,t):
    a,b,c=t;n=cross(sub(b,a),sub(c,a))
    need(any(n),'degenerate_triangle')
    if dot(sub(p,a),n)!=0:return False
    return all(dot(cross(sub(v,u),sub(p,u)),n)>=0 for u,v in((a,b),(b,c),(c,a)))

def intersection_segment(first,second):
    """Caller must establish proper crossing with the pinned original kernel."""
    a=tuple(exact(p)for p in first);b=tuple(exact(p)for p in second)
    na=cross(sub(a[1],a[0]),sub(a[2],a[0]));nb=cross(sub(b[1],b[0]),sub(b[2],b[0]));direction=cross(na,nb)
    need(any(na)and any(nb),'degenerate_triangle')
    need(any(direction),'coplanar_proper_crossing_not_supported')
    axis=max(range(3),key=lambda k:abs(direction[k]));pieces=[]
    for tri,normal,origin in((a,nb,b[0]),(b,na,a[0])):
        distances=[dot(sub(p,origin),normal)for p in tri];points=[]
        for i in range(3):
            j=(i+1)%3
            if distances[i]==0:points.append(tri[i])
            if distances[i]*distances[j]<0:
                t=distances[i]/(distances[i]-distances[j]);points.append(add(tri[i],mul(sub(tri[j],tri[i]),t)))
        need(len(set(points))>=2,'proper_kernel_exact_interval_disagreement')
        pieces.append((min(p[axis]for p in points),max(p[axis]for p in points),points[0]))
    lo=max(p[0]for p in pieces);hi=min(p[1]for p in pieces)
    need(hi>lo,'proper_kernel_exact_interval_disagreement')
    origin=pieces[0][2]
    return Segment(add(origin,mul(direction,(lo-origin[axis])/direction[axis])),add(origin,mul(direction,(hi-origin[axis])/direction[axis])))

class ClosedComponent:
    def __init__(self,triangles,side,label,face_ids=None):
        need(side in(-1,1),'invalid_component_side')
        self.side=side;self.label=label;self.triangles=np.asarray(triangles,dtype=np.float64)
        need(self.triangles.ndim==3 and self.triangles.shape[1:]==(3,3)and np.isfinite(self.triangles).all(),'invalid_component_geometry')
        self.lo=self.triangles.min(axis=1);self.hi=self.triangles.max(axis=1);self._exact={}
        self.face_ids=list(range(len(self.triangles)))if face_ids is None else list(face_ids)
        need(len(self.face_ids)==len(self.triangles)and len(set(self.face_ids))==len(self.face_ids),'component_face_identity')
        self.local_index={int(f):i for i,f in enumerate(self.face_ids)}
        edges={};vertices=set();normals=np.cross(self.triangles[:,1]-self.triangles[:,0],self.triangles[:,2]-self.triangles[:,0])
        need(np.all(np.linalg.norm(normals,axis=1)>0),'degenerate_component_face')
        for i,t in enumerate(self.triangles):
            q=[tuple(x)for x in t];need(len(set(q))==3,'collapsed_component_face');vertices.update(q)
            for a,b in zip(q,q[1:]+q[:1]):edges.setdefault(tuple(sorted((a,b))),[]).append((i,a,b))
        need(all(len(e)==2 and e[0][1:]==e[1][1:][::-1]for e in edges.values()),'component_not_closed_or_oriented')
        adjacency={i:set()for i in range(len(self.triangles))}
        for owners in edges.values():i,j=owners[0][0],owners[1][0];adjacency[i].add(j);adjacency[j].add(i)
        visited=set();stack=[0]
        while stack:
            i=stack.pop()
            if i in visited:continue
            visited.add(i);stack.extend(adjacency[i]-visited)
        need(len(visited)==len(self.triangles),'component_disconnected')
        need(len(vertices)-len(edges)+len(self.triangles)==2,'component_not_spherical_topology')
        volume=float(np.einsum('ij,ij->i',self.triangles[:,0],np.cross(self.triangles[:,1],self.triangles[:,2])).sum()/6)
        need(math.isfinite(volume)and volume>0,'component_not_outward')
        self.topology={'vertices':len(vertices),'edges':len(edges),'faces':len(self.triangles),'Euler':2,'closed_oriented':True}

    def triangle(self,i):
        if i not in self._exact:self._exact[i]=tuple(exact(p)for p in self.triangles[i])
        return self._exact[i]

    def _point_boxes(self,p):
        lo,hi=bounds([p]);return np.flatnonzero(np.all(self.lo<=hi[0],axis=1)&np.all(self.hi>=lo[0],axis=1))

    def _ray_boxes(self,p,direction):
        lo,hi=bounds([p]);near=np.full(len(self.triangles),-np.inf);far=np.full(len(self.triangles),np.inf)
        for k,d in enumerate(direction):
            need(d!=0,'zero_ray_axis')
            lower=np.nextafter(self.lo[:,k]-hi[0,k],-np.inf);upper=np.nextafter(self.hi[:,k]-lo[0,k],np.inf)
            if d>0:a=np.nextafter(lower/d,-np.inf);b=np.nextafter(upper/d,np.inf)
            else:a=np.nextafter(upper/d,-np.inf);b=np.nextafter(lower/d,np.inf)
            near=np.maximum(near,a);far=np.minimum(far,b)
        return np.flatnonzero(far>=np.maximum(near,0))

    def _ray_parity(self,p,direction):
        ray=tuple(Q(x)for x in direction);hits=set()
        for i in self._ray_boxes(p,direction):
            tri=self.triangle(int(i));n=cross(sub(tri[1],tri[0]),sub(tri[2],tri[0]));den=dot(n,ray);numerator=dot(n,sub(tri[0],p))
            if den==0:
                need(numerator!=0,'grazing_ray_direction');continue
            t=numerator/den
            if t<=0:continue  # exact sign, with NO distance cutoff
            q=add(p,mul(ray,t))
            if not on_triangle(q,tri):continue
            orientation=[dot(cross(sub(v,u),sub(q,u)),n)for u,v in((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0]))]
            need(all(x!=0 for x in orientation),'grazing_ray_direction')
            hits.add(t)
        return len(hits)%2==1,len(hits)

    def location(self,point):
        p=exact(point)
        for i in self._point_boxes(p):
            if on_triangle(p,self.triangle(int(i))):return 'BOUNDARY'
        counts=[];parities=[]
        for ray in RAYS:
            try:inside,count=self._ray_parity(p,ray)
            except Rejected as error:
                if error.code=='grazing_ray_direction':continue
                raise
            parities.append(inside);counts.append(count)
            if len(parities)==3:break
        need(len(parities)==3 and len(set(parities))==1,'parity_ambiguity',counts)
        q=self.triangles-np.asarray([float(x)for x in p]);a,b,c=q[:,0],q[:,1],q[:,2];length=np.linalg.norm(q,axis=2)
        numerator=np.einsum('ij,ij->i',a,np.cross(b,c));denominator=np.prod(length,axis=1)+np.einsum('ij,ij->i',a,b)*length[:,2]+np.einsum('ij,ij->i',b,c)*length[:,0]+np.einsum('ij,ij->i',c,a)*length[:,1]
        winding=float(np.sum(2*np.arctan2(numerator,denominator))/(4*np.pi));expected=1. if parities[0]else 0.
        need(math.isfinite(winding)and abs(winding-expected)<=1e-7,'winding_parity_disagreement',winding)
        return 'INSIDE'if parities[0]else'OUTSIDE'

    def segment_events(self,segment):
        lo,hi=bounds([segment.a,segment.b]);candidates=np.flatnonzero(np.all(self.lo<=hi.max(axis=0),axis=1)&np.all(self.hi>=lo.min(axis=0),axis=1));events={Q(0),Q(1)};direction=sub(segment.b,segment.a)
        for i in candidates:
            tri=self.triangle(int(i));n=cross(sub(tri[1],tri[0]),sub(tri[2],tri[0]));den=dot(n,direction);numerator=dot(n,sub(tri[0],segment.a))
            if den==0:
                need(numerator!=0,'coplanar_segment_surface_contact_not_supported');continue
            t=numerator/den
            if 0<=t<=1 and on_triangle(segment.point(t),tri):events.add(t)
        return sorted(events)

    def split(self,segment):
        cuts=self.segment_events(segment);pieces=[]
        for lo,hi in zip(cuts,cuts[1:]):
            need(hi>lo,'unresolved_event_interval')
            pieces.append((lo,hi,self.location(segment.point((lo+hi)/2))))
        return pieces

    def contained(self,segment):
        need(self.location(segment.a)!='OUTSIDE'and self.location(segment.b)!='OUTSIDE','exterior_segment_endpoint')
        intervals=self.split(segment)
        need(all(location in('INSIDE','BOUNDARY')for _,_,location in intervals),'exterior_segment_interval')
        return {'full_segment_contained':True,'event_intervals':[[float(a),float(b),s]for a,b,s in intervals]}

    def clipped_inside(self,segment):
        return [Segment(segment.point(a),segment.point(b))for a,b,s in self.split(segment)if s in('INSIDE','BOUNDARY')]

def max_distance_certificate(segment,targets,limit):
    """Outward interval arithmetic plus a full1-Lipschitz covering certificate."""
    need(targets,'missing_source_reference_curve');need(limit in(BODY_LIMIT,CONTACT_LIMIT),'unsupported_distance_limit')
    a=bounds([segment.a]);b=bounds([segment.b]);length_upper=float(norm_upper(isub(b,a))[0]);need(math.isfinite(length_upper)and length_upper>0,'invalid_locus_length')
    cells=max(1,math.ceil(length_upper/(2*CELL_HALF_ARC_M)));need(cells<=1000000,'distance_certificate_cell_budget')
    tb=np.asarray([scalar_bounds(Q(2*i+1,2*cells))for i in range(cells)])
    points=iadd(a,imul(isub(b,a),(tb[:,0,None],tb[:,1,None])))
    ta=bounds([t.a for t in targets]);te=bounds([t.b for t in targets]);delta=isub(te,ta)
    approx_p=(points[0]+points[1])*.5;approx_a=(ta[0]+ta[1])*.5;approx_v=(delta[0]+delta[1])*.5
    squared=np.einsum('ki,ki->k',approx_v,approx_v);need(np.all(squared>0),'degenerate_source_reference')
    projections=np.clip(np.einsum('nki,ki->nk',approx_p[:,None,:]-approx_a[None,:,:],approx_v)/squared[None,:],0,1);need(np.isfinite(projections).all(),'nonfinite_projection')
    targets_at=iadd((ta[0][None,:,:],ta[1][None,:,:]),imul((delta[0][None,:,:],delta[1][None,:,:]),(projections[:,:,None],projections[:,:,None])))
    differences=isub((points[0][:,None,:],points[1][:,None,:]),targets_at)
    midpoint_upper=float(norm_upper(differences).min(axis=1).max())
    cover=np.nextafter(length_upper/(2*cells),np.inf);upper=float(np.nextafter(np.nextafter(midpoint_upper+cover,np.inf)+ARITHMETIC_RESERVE_M,np.inf))
    need(math.isfinite(upper),'nonfinite_distance_certificate')
    need(Q.from_float(upper)<=limit,'whole_locus_distance_limit',{'upper_m':upper,'limit_m':float(limit)})
    return {'upper_m':upper,'limit_m':float(limit),'cells':cells,'midpoint_upper_m':midpoint_upper,'half_cell_arc_upper_m':float(cover),'arithmetic_reserve_m':ARITHMETIC_RESERVE_M,'method':'outward interval distance to valid source-segment points + complete1-Lipschitz cell cover'}

def admit_body_crossing(segment,patch_side,other_face,other_triangle,parent_other_triangle,component,allowed_faces,source_curves,both_replaced=False):
    need(not both_replaced,'patch_patch_crossing_forbidden')
    need(component.side==patch_side,'wrong_side_component')
    need(other_face in allowed_faces,'undeclared_original_interface_face',other_face)
    need(np.array_equal(other_triangle,parent_other_triangle),'changed_original_interface_face')
    containment=component.contained(segment)
    certificate=max_distance_certificate(segment,source_curves,BODY_LIMIT)
    return {'original_unchanged_face':int(other_face),'side':patch_side,**containment,'locus_certificate':certificate}

def admit_globe_contact(segment,patch_side,component,source_curves,globe_face):
    need(component.side==patch_side,'wrong_side_globe_contact')
    need(globe_face in component.local_index,'undeclared_globe_component_face')
    triangle=component.triangle(component.local_index[globe_face])
    need(on_triangle(segment.a,triangle)and on_triangle(segment.b,triangle),'contact_not_on_attested_globe_face')
    return {'side':patch_side,'globe_face':int(globe_face),'new_contact_not_inherited':True,'locus_certificate':max_distance_certificate(segment,source_curves,CONTACT_LIMIT)}
