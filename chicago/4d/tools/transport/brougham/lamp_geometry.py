# SPDX-License-Identifier: GPL-3.0-or-later
"""V18 exact lamp surface and protected V17 stream readback; original numerical guards retained."""
import collections,hashlib,json,math,struct
from check_mid import bind_parts
OLD={'lamp_glass','lamp_frame_ring','lamp_corner_stile','lamp_pitched_cap','lamp_finial'}
NEW={'lamp_rounded_upper_shell','lamp_hidden_inner_back','lamp_outward_oval_bright_surround',
 'lamp_outward_oval_reveal','lamp_outward_oval_glass','lamp_forward_oval_bright_surround',
 'lamp_forward_oval_reveal','lamp_forward_oval_glass','lamp_narrow_lower_glass',
 'lamp_lower_corner_stile','lamp_lower_base','lamp_finial'}
EXPECTED_OWNED={name:(8 if name=='lamp_lower_corner_stile'else 2)for name in NEW}
EXPECTED_MATERIAL={name:(3 if name.endswith('bright_surround')or name=='lamp_finial'else 5 if name.endswith('glass')else 4)for name in NEW}

def require(ok,why):
 if not ok:raise AssertionError(why)

def keyed(j,b):
 counts=collections.Counter();out={}
 for row in bind_parts(j,b):
  base=tuple(row['identity'][:3]);key=base+(counts[base],);counts[base]+=1
  require(key not in out,'Duplicate occurrence identity');out[key]=row
 return out

def protected(rows,owned):return {k:v for k,v in rows.items()if k[0]not in owned}

def digest_rows(rows):
 h=hashlib.sha256()
 for key,row in rows.items():
  h.update(json.dumps(key,separators=(',',':')).encode())
  for a in ['POSITION','NORMAL']:h.update(row['chunks'][a])
 return h.hexdigest()

def vector(a,b):return tuple(x-y for x,y in zip(a,b))

def dot(a,b):return sum(x*y for x,y in zip(a,b))

def cross(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

def average(points):return tuple(sum(p[k]for p in points)/len(points)for k in range(3))

def point_rows(row):return list(struct.iter_unpack('<fff',row['chunks']['POSITION']))

def native_box(points):return{'min':[min(p[k]for p in points)for k in range(3)],'max':[max(p[k]for p in points)for k in range(3)]}

def contained(a,c):return all(a['min'][k]<=c['min'][k]and c['max'][k]<=a['max'][k]for k in range(3))

def lamp_surfaces(rows,params):
 counts=collections.Counter(k[0]for k in rows if k[0]in NEW)
 require(dict(counts)==EXPECTED_OWNED,'Exact new lamp occurrence families required')
 affine=params['body_vertical_affine'];height=lambda y:y*affine['scale_y']+affine['offset_y_m']
 checked=0
 for key,row in rows.items():
  name=key[0]
  if name not in NEW:continue
  require(row['identity'][1]=='vehicle_body'and row['identity'][2]==EXPECTED_MATERIAL[name],'Unexpected lamp carrier/material')
  ps=point_rows(row);ns=list(struct.iter_unpack('<fff',row['chunks']['NORMAL']));side=1 if average(ps)[0]>0 else-1
  center=(side*.60,height(1.53+.0875),.44)
  if name=='lamp_narrow_lower_glass':center=(side*.60,height(1.53-.0525),.44)
  elif name in ['lamp_lower_corner_stile','lamp_lower_base','lamp_finial']:center=average(ps)
  for i in range(0,len(ps),3):
   tri=ps[i:i+3];normal=cross(vector(tri[1],tri[0]),vector(tri[2],tri[0]));m=math.sqrt(dot(normal,normal))
   require(m*m>1e-20,'Tiny/degenerate lamp triangle not waived');unit=tuple(v/m for v in normal);centroid=average(tri)
   require(all(dot(unit,n)>=1-1e-4 for n in ns[i:i+3]),'Lamp geometric/shading normal disagreement')
   if name.startswith('lamp_outward_oval')and not name.endswith('reveal'):require(unit[0]*side>=1-1e-4,'Outward-side aperture faces inward')
   elif name.startswith('lamp_forward_oval')and not name.endswith('reveal'):require(unit[2]>=1-1e-4,'Forward aperture faces backward')
   elif name=='lamp_hidden_inner_back':require(unit[0]*(-side)>=1-1e-4,'Hidden inner back faces inward')
   elif name.endswith('reveal'):
    inward=list(vector(center,centroid));inward[0 if name.startswith('lamp_outward')else 2]=0.
    require(dot(unit,inward)>0,'Aperture reveal faces into solid case')
   else:require(dot(unit,vector(centroid,center))>0,'Convex lamp shell/stem/cap faces inward')
   checked+=1
 # Check actual serialized shared aperture vertices, including recessed glass joins.
 for prefix in ['lamp_outward_oval','lamp_forward_oval']:
  for ordinal in [0,1]:
   def lookup(suffix):return next(v for k,v in rows.items()if k[0]==prefix+suffix and k[3]==ordinal)
   surround=set(point_rows(lookup('_bright_surround')));reveal=set(point_rows(lookup('_reveal')));glass=set(point_rows(lookup('_glass')))
   require(len(surround)==24 and len(reveal)==24 and len(glass)==12,'Aperture distinct serialized-vertex inventory')
   require(glass<=reveal and len(reveal-glass)==12 and reveal-glass<=surround,'Recessed lens/reveal/surround vertex seam does not meet')
 return checked

def protected_signatures_v18(j,b):
 rows=keyed(j,b);kept=protected(rows,NEW)
 require(len(kept)==450,'Exact protected V17 non-lamp occurrence inventory')
 require(not any(k[0]in OLD-{'lamp_finial'} for k in rows),'Superseded lamp family returned')
 parents={c:i for i,n in enumerate(j['nodes'])for c in n.get('children',[])};nodes={n['mesh']:i for i,n in enumerate(j['nodes'])if 'mesh'in n}
 h=hashlib.sha256();streams=0
 for i,m in enumerate(j['meshes']):
  prim=m['primitives'][0]
  if(parents[nodes[i]],prim['material'])in[(1,3),(1,4),(1,5)]:continue
  h.update(json.dumps([i,m['name']],separators=(',',':')).encode())
  for kind in ['POSITION','NORMAL']:
   a=j['accessors'][prim['attributes'][kind]];v=j['bufferViews'][a['bufferView']];require(a['componentType']==5126 and a['type']=='VEC3'and not v.get('byteStride'),'Actual raw float32 source stream')
   off=v.get('byteOffset',0)+a.get('byteOffset',0);h.update(b[off:off+a['count']*12]);streams+=1
 require(streams==44,'Exactly22 protected non-lamp raw batches')
 return{'parts':len(kept),'protected_part_PN_sha256':digest_rows(kept),'mesh_streams':streams,'protected_mesh_PN_sha256':h.hexdigest()}
