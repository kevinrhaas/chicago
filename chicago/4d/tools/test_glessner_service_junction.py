"""T-2219: photographed service openings remain whole at the stable roof join."""
from pathlib import Path
import copy
import json
import math
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'generators'))
from archetypes.masonry_house_params import from_phase
from archetypes.masonry_house_v4_west_roof import height, patches
r=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
p=from_phase(r['phases'][0],r)
w=next(x for x in p.ranges if x['name']=='west_wing')
n=next(x for x in p.ranges if x['name']=='north_range')
d=p.detail['north_service_junction']
door=next(o for o in p.openings if o.get('style')=='service_door' and o['face']=='north')
upper=next(o for o in p.openings if o['face']=='north' and o['kind']=='window' and abs(o['u1']-door['u1'])<.01)
neighbour=next(o for o in p.openings if o['face']=='north' and o['kind']=='window' and upper['u1']<o['u0']<upper['u1']+2 and abs(o['z0']-upper['z0'])<.01)
# Independent HABS02/03/15 proportion: these two openings are about as wide
# as the neighbouring four-foot sash, not the former 2.4-foot slit.
width=lambda o:o['u1']-o['u0']
assert .88<width(door)/width(neighbour)<1.08
assert .95<width(upper)/width(neighbour)<1.12
assert abs(w['x1']-(161.25-125.75)*.3048)<1e-4,'Courtyard footprint moved'
assert n['north_wall_min']<upper['u0']-.15
assert w['stable_roof']['front_x1']<door['u0']-.25
assert 0<d['step_heights'][0]<d['step_heights'][1]
assert abs(d['step_heights'][-1]-door['z0'])<1e-4
assert d['step_x'][0]<door['u0']<door['u1']<d['step_x'][1]
assert d['step_runs'][0]>d['step_runs'][1]>0
# Shared roof edges must agree from both wings, including the street overhang.
# Small independent changes to the front gable must not open a seam or change
# the existing courtyard roof, which is a separate owner-approved silhouette.
for shift in (-.03,0,.03):
 q=copy.deepcopy(w);g=q['stable_roof'];g['front_x1']+=shift
 assert abs(height(q,g['front_x1'],q['y1'])-n['eave_hi_z'])<1e-5
 for i in range(101):
  y=n['ridge_at']+(n['y1']+.20-n['ridge_at'])*i/100
  expected=n['ridge_z']+(n['eave_hi_z']-n['ridge_z'])*(y-n['ridge_at'])/(n['y1']-n['ridge_at'])
  assert abs(height(q,g['court_edge_x'],y)-expected)<1e-5,(shift,y)
 for _,poly in patches(q,False):
  if max(v[1] for v in poly)>q['y1']+1e-5:
   assert min(v[0] for v in poly)>=g['front_x1']-1e-7,'Roof shelf crosses gable face'
 # A two-sided eave is closed by the edge generator; it has no vertical gap
 # where the new roof return meets the ordinary north roof's western edge.
 assert math.isfinite(height(q,g['court_edge_x'],n['y1']))
print('PASS: full service apertures, preserved courtyard footprint, threshold steps, continuous roof seam and no gable-crossing eave')
