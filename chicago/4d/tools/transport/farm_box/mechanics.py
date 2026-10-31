# SPDX-License-Identifier: GPL-3.0-or-later
"""Read actual indexed geometry; never substitute construction parameters for it."""
import json
import math
import re
import struct
from pathlib import Path
import numpy as np


def wagon_code_regions(text):
    """Exact existing wagon functions/dependencies, excluding unrelated actors.

    This source has top-level function declarations whose closing brace begins
    a line (or an entire one-line declaration). Retain exact bytes, not a claim
    of JavaScript semantic equivalence. Conservative dependencies found in
    comments may add protected functions; none remove actual call matches.
    """
    declarations=list(re.finditer(r'^function ([A-Za-z_$][\w$]*)\(',text,re.M))
    functions={}
    for i,m in enumerate(declarations):
        block=text[m.start():declarations[i+1].start() if i+1<len(declarations) else len(text)]
        close=block.rfind('\n}')
        functions[m[1]]=block[:close+2] if close>=0 else block.split('\n',1)[0]
    selected={'wagonCoat','pushWagonBox','buildWagon','buildCart','pushYoke','readForm'}
    while True:
        calls=set(re.findall(r'\b([A-Za-z_$][\w$]*)\s*\(', '\n'.join(functions[n]for n in selected)))
        expanded=selected|(calls&functions.keys())
        if expanded==selected:
            break
        selected=expanded
    regions={f'function:{n}':functions[n]for n in sorted(selected)}
    constants=list(re.finditer(r'^const ([A-Z][A-Z0-9_]*)\s*=',text,re.M))
    values={m[1]:text[m.start():text.index(';',m.end())+1]for m in constants}
    while True:
        used=set(re.findall(r'\b[A-Z][A-Z0-9_]*\b','\n'.join(regions.values())))&values.keys()
        additions={f'constant:{n}':values[n]for n in used}
        if all(k in regions for k in additions):
            break
        regions.update(additions)
    return regions


class Master:
    def __init__(self, path):
        self.raw = Path(path).read_bytes()
        if struct.unpack_from('<III', self.raw) != (0x46546c67, 2, len(self.raw)):
            raise ValueError('Invalid master GLB2')
        size, kind = struct.unpack_from('<II', self.raw, 12)
        if kind != 0x4e4f534a:
            raise ValueError('Master JSON missing')
        self.g = json.loads(self.raw[20:20+size])
        length, kind = struct.unpack_from('<II', self.raw, 20+size)
        self.binary = self.raw[28+size:]
        if kind != 0x004e4942 or length != len(self.binary):
            raise ValueError('Master BIN framing')
        self.parents = {c:i for i,n in enumerate(self.g['nodes']) for c in n.get('children',[])}
        self.names = {n['name']:i for i,n in enumerate(self.g['nodes'])}
        if len(self.names) != len(self.g['nodes']):
            raise ValueError('Duplicate frame names')
        self.meshes = {m['name']:m for m in self.g['meshes']}

    def accessor(self, index):
        a = self.g['accessors'][index]
        v = self.g['bufferViews'][a['bufferView']]
        if a.get('sparse') or v.get('extensions'):
            raise ValueError('Mechanical master must use explicit uncompressed attributes')
        dtype = np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']])
        width = {'VEC2':2,'VEC3':3,'VEC4':4,'SCALAR':1}[a['type']]
        stride = v.get('byteStride',width*dtype.itemsize)
        offset = a.get('byteOffset',0)
        if offset+(a['count']-1)*stride+width*dtype.itemsize > v['byteLength']:
            raise ValueError('Accessor outside buffer view')
        return np.ndarray((a['count'],width),dtype=dtype,buffer=self.binary,
                          offset=v.get('byteOffset',0)+offset,
                          strides=(stride,dtype.itemsize)).copy()

    def positions(self, name):
        return self.accessor(self.meshes[name]['primitives'][0]['attributes']['POSITION']).astype(float)

    def triangles(self, name):
        p = self.meshes[name]['primitives'][0]
        return self.positions(name)[self.accessor(p['indices']).reshape(-1,3)]

    def translation(self, name):
        i = self.names[name]
        n = self.g['nodes'][i]
        if any(k in n for k in ['rotation','scale','matrix']):
            raise ValueError('Unexpected rest-frame transform')
        return np.array(n.get('translation',[0,0,0]),dtype=float)+(self.translation(self.g['nodes'][self.parents[i]]['name']) if i in self.parents else 0)


def clip(poly, axis, bound, keep_more):
    out = []
    for q,r in zip(poly,np.roll(poly,-1,axis=0)):
        iq = q[axis]>=bound if keep_more else q[axis]<=bound
        ir = r[axis]>=bound if keep_more else r[axis]<=bound
        if iq:
            out.append(q)
        if iq != ir:
            out.append(q+(r-q)*((bound-q[axis])/(r[axis]-q[axis])))
    return np.array(out)


def front_swept_clearance(body, wheel_points, centre, side, limit_deg):
    """Conservative separation for ALL roll phases and steering angles.

    Each actual wheel triangle lies in the convex cylinder bounded by its
    actual vertex radii and axial extrema. Rotating that cylinder bounds
    every wheel phase. Clip actual body triangles into 5mm Y bands and a
    conservative swept Z slab. A positive X separator proves disjointness;
    a nonpositive result is inconclusive and must never be called collision.
    Hubs/bores that intentionally meet axles are excluded by source ownership.
    """
    radius = float(np.hypot(wheel_points[:,1],wheel_points[:,2]).max())
    axial_min = centre[0]*side+float((wheel_points[:,0]*side).min())
    axial_max = centre[0]*side+float((wheel_points[:,0]*side).max())
    angle = math.radians(limit_deg)
    if not 0<=angle<math.pi/2 or axial_min<=0:
        raise ValueError('Unsupported turn envelope')
    zlo = centre[2]-radius-axial_max*math.sin(angle)
    zhi = centre[2]+radius+axial_max*math.sin(angle)
    bmin,bmax = body.min(axis=1),body.max(axis=1)
    margins = []
    for lo in np.arange(max(centre[1]-radius,float(bmin[:,1].min())),centre[1]+radius,.005):
        hi = min(lo+.005,centre[1]+radius)
        dy = 0 if lo<=centre[1]<=hi else min(abs(lo-centre[1]),abs(hi-centre[1]))
        radial_z = math.sqrt(max(0,radius*radius-dy*dy))
        wheel_min = axial_min*math.cos(angle)-radial_z*math.sin(angle)
        candidates = body[(bmax[:,1]>=lo)&(bmin[:,1]<=hi)&(bmax[:,2]>=zlo)&(bmin[:,2]<=zhi)]
        body_max = -math.inf
        for tri in candidates:
            p = tri
            for axis,bound,more in [(1,lo,True),(1,hi,False),(2,zlo,True),(2,zhi,False)]:
                if not len(p):
                    break
                p = clip(p,axis,bound,more)
            if len(p):
                body_max = max(body_max,float((p[:,0]*side).max()))
        if body_max != -math.inf:
            margins.append({'y_band_m':[float(lo),float(hi)],'gap_m':float(wheel_min-body_max)})
    if not margins:
        raise ValueError('Empty clearance comparison')
    return {'radius_bound_m':radius,'minimum_gap_m':min(r['gap_m']for r in margins),
            'worst':min(margins,key=lambda r:r['gap_m']),
            'scope':'All wheel roll phases and every steer angle within declared limit; actual tyre/eight-spoke geometry vs actual body/frame, excluding intended axle/hub interfaces'}


def intersections(a, b):
    """Triangle SAT including in-plane axes for coplanar triangles."""
    amin,amax,bmin,bmax = a.min(axis=1),a.max(axis=1),b.min(axis=1),b.max(axis=1)
    ia,ib = np.where(np.all(amax[:,None,:]>=bmin[None,:,:]-1e-9,axis=2)&np.all(amin[:,None,:]<=bmax[None,:,:]+1e-9,axis=2))
    if not len(ia):
        return []
    A,B = a[ia],b[ib]
    ea,eb = np.roll(A,-1,axis=1)-A,np.roll(B,-1,axis=1)-B
    na,nb = np.cross(ea[:,0],ea[:,1]),np.cross(eb[:,0],eb[:,1])
    axes = [na,nb]+[np.cross(ea[:,i],eb[:,j])for i in range(3)for j in range(3)]
    axes += [np.cross(na,ea[:,i])for i in range(3)]+[np.cross(nb,eb[:,i])for i in range(3)]
    alive = np.ones(len(ia),dtype=bool)
    for axis in axes:
        norms = np.linalg.norm(axis,axis=1)
        valid = norms>1e-14
        axis = axis/np.maximum(norms[:,None],1e-30)
        pa,pb = np.einsum('nvi,ni->nv',A,axis),np.einsum('nvi,ni->nv',B,axis)
        alive &= ~(valid&((pa.max(axis=1)<pb.min(axis=1)-1e-8)|(pb.max(axis=1)<pa.min(axis=1)-1e-8)))
    return [(int(i),int(j))for i,j in zip(ia[alive],ib[alive])]
