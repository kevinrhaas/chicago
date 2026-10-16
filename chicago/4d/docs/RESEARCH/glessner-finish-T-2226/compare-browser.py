import json
from pathlib import Path
p=Path('/workspace/t2226-proof');rows=[]
for tier,label in [('full','desktop'),('mobile','mobile')]:
 before=json.loads((p/f'before-{tier}/browser-validation-{label}.json').read_text())['results'][0]
 after=json.loads((p/f'after-{tier}/browser-validation-{label}.json').read_text())['results'][0]
 assert before['viewport']==after['viewport'] and before['detail']==after['detail']
 assert not after['errors'] and not after['bad'] and all(not s['problems'] for s in after['stands'])
 a={(s['name'],s['light']):s for s in before['stands']};b={(s['name'],s['light']):s for s in after['stands']};assert a.keys()==b.keys()
 for key,x in a.items():
  y=b[key]
  for field in ['camera','cameraQuaternion','projection','exposure','glassModes']:
   assert x[field]==y[field],(tier,key,field,'Diagnostic control changed')
  assert y['lightingRestored']
  assert x['stats']['budget']==y['stats']['budget'],'Budget changed'
  rows.append({'tier':after['detail'],'view':key[0],'light':key[1],'before_calls':x['stats']['drawCalls'],'after_calls':y['stats']['drawCalls'],'before_triangles':x['stats']['triangles'],'after_triangles':y['stats']['triangles'],'before_pass':x['stats']['withinBudget'],'after_pass':y['stats']['withinBudget'],'controls_unchanged':True,'lighting_restored':True})
(p/'browser-comparison.json').write_text(json.dumps({'method':'Actual published app, same frozen cameras/projection/exposure and dark-glass mode; exact lighting restoration; unchanged budget thresholds. These are count/capture results, not physical-GPU FPS or a visual acceptance substitute.','rows':rows},indent=2)+'\n')
print(json.dumps(rows,indent=2))
