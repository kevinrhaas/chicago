# SPDX-License-Identifier: CC0-1.0
"""Original small GLB append-only binary adapter for this indexed skin study."""
import json,struct,copy
import numpy as np
from planar import need
DT={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}
NC={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def parse(raw):
 need(len(raw)>=28,'Short GLB');magic,version,total=struct.unpack_from('<III',raw);need(magic==0x46546c67 and version==2 and total==len(raw),'Invalid GLB header');n,kind=struct.unpack_from('<II',raw,12);need(kind==0x4e4f534a,'Missing JSON');d=json.loads(raw[20:20+n]);bn,bk=struct.unpack_from('<II',raw,20+n);need(bk==0x004e4942 and 28+n+bn==len(raw),'Missing/inconsistent BIN');need(len(d['buffers'])==1 and'uri'not in d['buffers'][0],'External buffer forbidden');return d,bytearray(raw[28+n:])
def read(d,b,i):
 need(isinstance(i,int)and 0<=i<len(d['accessors']),'Accessor index out of bounds');a=d['accessors'][i];need('sparse'not in a and not a.get('normalized',False),'Sparse/normalized accessor unsupported');need(0<=a['bufferView']<len(d['bufferViews']),'Accessor view index out of bounds');v=d['bufferViews'][a['bufferView']];need(v.get('buffer',0)==0 and len(d['buffers'])==1,'Unexpected buffer index');need('byteStride'not in v,'Strided accessor unsupported');need(a['componentType']in DT and a['type']in NC,'Accessor contract');size=NC[a['type']];view_start=v.get('byteOffset',0);accessor_start=a.get('byteOffset',0);length=a['count']*size*np.dtype(DT[a['componentType']]).itemsize;need(isinstance(a['count'],int)and a['count']>=0 and view_start>=0 and accessor_start>=0 and v['byteLength']>=0,'Negative/nonintegral accessor extent');need(accessor_start+length<=v['byteLength'],'Accessor exceeds its own view');need(view_start+v['byteLength']<=len(b)and view_start+v['byteLength']<=d['buffers'][0]['byteLength'],'View exceeds declared buffer');off=view_start+accessor_start;need(off%np.dtype(DT[a['componentType']]).itemsize==0,'Unaligned accessor');arr=np.frombuffer(b,dtype=DT[a['componentType']],count=a['count']*size,offset=off).copy().reshape(a['count'],size);need(np.isfinite(arr).all(),'Nonfinite accessor');return arr

def append(d,b,values,typ,comp=5126,target=34962):
 a=np.asarray(values,dtype=DT[comp]).reshape(-1,NC[typ]);need(len(a)>0 and np.isfinite(a).all(),'Empty/nonfinite new accessor')
 while len(b)%4:b.append(0)
 vi=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':a.nbytes,'target':target});b.extend(a.tobytes());i=len(d['accessors']);entry={'bufferView':vi,'componentType':comp,'count':len(a),'type':typ}
 if typ in['VEC3','SCALAR']:entry.update(min=a.min(0).tolist(),max=a.max(0).tolist())
 d['accessors'].append(entry);d.setdefault('buffers',[{'byteLength':len(b)}]);need(len(d['buffers'])==1,'Append requires one buffer');d['buffers'][0]['byteLength']=len(b);return i

def encode(d,b):
 # This function is authored but NOT executed on any horse candidate yet.
 d=copy.deepcopy(d);d['buffers'][0]['byteLength']=len(b);jb=json.dumps(d,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);bb=bytes(b)+b'\0'*((-len(b))%4);return struct.pack('<III',0x46546c67,2,28+len(jb)+len(bb))+struct.pack('<II',len(jb),0x4e4f534a)+jb+struct.pack('<II',len(bb),0x004e4942)+bb
