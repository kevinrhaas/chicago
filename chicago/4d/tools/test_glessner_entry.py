"""HABS5/doorway23A entry-section checks on emitted geometry, not screenshots."""
from pathlib import Path
import json,math,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from _glessner_lod import _geometry_modules
d,pm,_=_geometry_modules(ROOT)
r=json.loads((ROOT/'data/structures/glessner_house.json').read_text());p=pm.from_phase(r['phases'][0],r)
s=p.detail['prairie_entry'];x=p.width_m
b=d.DetailBuilder('entry-test',p)
b.wall([(x,10,0),(x,15,0),(x,15,3),(x,10,3)],1,0)
assert b.entry_return_faces,'Lower cut edges are open'
for ids in b.faces:
    pts=[b.verts[i] for i in ids]
    assert math.sqrt(sum(v*v for v in d.legacy._normal(pts)))>1e-12,'Degenerate entry face'
# Intersect an exterior-normal ray with the actual emitted wall facets.
def depths(u,z):
    found=[]
    for ids in b.faces:
        pts=[b.verts[i] for i in ids]
        for j in range(1,len(pts)-1):
            a,c,e=pts[0],pts[j],pts[j+1]
            den=(c[2]-e[2])*(a[1]-e[1])+(e[1]-c[1])*(a[2]-e[2])
            if abs(den)<1e-12:continue
            ta=((c[2]-e[2])*(u-e[1])+(e[1]-c[1])*(z-e[2]))/den
            tc=((e[2]-a[2])*(u-e[1])+(a[1]-e[1])*(z-e[2]))/den;te=1-ta-tc
            if min(ta,tc,te)>-1e-8:found.append(ta*a[0]+tc*c[0]+te*e[0]-x)
    return found
# HABS section: outer lower stones project, both cutback panels remain behind them.
for u in (10.5,14.5):assert max(depths(u,.5))>.13,'Lower exterior lacks its outward slope'
for u in (11.35,13.7):assert -.02<max(depths(u,.5))<.12,'Cutback panel is not recessed'
assert not depths(s['centre_u'],.7),'Wall covers the retained door aperture'

from archetypes.masonry_house_v4_frontage import add_frontage
class Capture:
    def __init__(self):self.faces=[]
    def raw(self,pts,conf,mat,want=None):self.faces.append((pts,mat,want))
c=Capture();add_frontage(c,p)
f=p.detail['prairie_frontage'];horizontal=[]
for pts,mat,want in c.faces:
    if mat!=2 or max(v[2] for v in pts)-min(v[2] for v in pts)>1e-8:continue
    if max(v[0] for v in pts)<x-.3 or min(v[0] for v in pts)>x+1:continue
    if min(v[1] for v in pts)>s['centre_u'] or max(v[1] for v in pts)<s['centre_u']:continue
    if pts[0][2]>f['walk_z']+.01:horizontal.append((pts,pts[0][2]))
assert len(horizontal)==1,'More than one raised tread at the entrance'
pts,level=horizontal[0]
assert abs(level-s['sill_z'])<1e-8
assert min(v[0] for v in pts)<x-.28 and max(v[0] for v in pts)<x+.20,'Threshold projects as a stoop'
assert max(v[1] for v in pts)-min(v[1] for v in pts)>2.7,'Threshold narrowed to the leaf'
assert f['entry_y'][0]<min(v[1] for v in pts) and f['entry_y'][1]>max(v[1] for v in pts),'Curb blocks tread'

fan=next(o for o in p.openings if o['kind']=='fan');fb=d.DetailBuilder('fan-test',p);d.ornament.fan(fb,fan)
cx=(fan['u0']+fan['u1'])/2;cz=fan['spring_z'];rr=fan['r_in']+.04
field=[v[0]-x for v in fb.verts if math.hypot(v[1]-cx,v[2]-cz)<rr*.60 and v[2]>cz+.05]
assert field and max(field)<-.18 and min(field)<-.30,'Carving or its bed floats at the facade'
assert max(field)-min(field)>.04,'Carving flattened against its recessed backing'
# T-2912: HABS sheet 5 draws the head stilted, its centre about 0.5 ft over the spring
# line and both rings plumb below it; the springers must reach the spring, not stop at
# the centre, and the field's rings are the sheet's eight.
st=fan.get('stilt',0)
assert .12<st<.18,'Fan lost its stilt'
legs=[v[2]-cz for v in fb.verts if abs(abs(v[1]-cx)-fan['r_out'])<.02 and cz-.01<v[2]<cz+st]
assert legs and min(legs)<.03 and max(legs)>st*.5,'Springers do not run plumb to the spring line'
assert len(d.ornament.FIELD_ROUNDELS)==8 and all(math.hypot(x,z)+r<1 for x,z,r in d.ornament.FIELD_ROUNDELS),'Field rings leave the field'
head=next(o for o in p.openings if o.get('style')=='rock_faced_lintel')
from archetypes.masonry_house_v4_entry import lintel_outline
poly=lintel_outline(head,s)
# T-2972: sheet 5 draws the header one course, door head to bed 8, its top flat to the
# shoulders and raised only under the tympanum, about 0.14 ft at the centre.
top=[q for q in poly[2:]]
crown=max(z for _,z in top);shoulder=poly[2][1]
assert poly[0][1]==poly[1][1] and poly[-1][1]==shoulder,'Header lost its level bearing or flat shoulders'
assert .03<crown-shoulder<.06,'Header crown is not the sheet\'s shallow rise'
raised=[u for u,z in top if z>shoulder+1e-6]
cx=(head['u0']+head['u1'])/2
assert raised and max(abs(u-cx) for u in raised)<fan['r_in'],'Header crown spreads past the tympanum'
assert abs(fan['spring_z']-shoulder)<.005,'Fan does not spring from the header\'s shoulders'
print('PASS: emitted cutback and outward wall slope, open door, one inset tread and recessed raised carving')
