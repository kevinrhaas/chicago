from pathlib import Path
from PIL import Image
import json, hashlib, os
import numpy as np
root=Path(os.environ.get('QA_COMPARE_DIR',str(Path(__file__).parent/'season')))
pairs=[(f'mobile-{name}.png',f'mobile-{name}-occlusion-off.png')for name in os.environ.get('QA_COMPARE_VIEWS','courtyard').split(',')]
pairs += [(f'mobile-season-{season}-on.png',f'mobile-season-{season}-off.png')for season in ['winter','summer']]
pairs += [(f'mobile-season-{season}-{a}.png',f'mobile-season-{season}-{b}.png') for season in ['winter','summer'] for a,b in [('on','repeatOn'),('off','repeatOff'),('on','restoredOn')]]
pairs += [('mobile-season-before.png','mobile-season-restored.png')]
rows=[]
for a,b in pairs:
    pa,pb=root/a,root/b
    if not pa.exists()or not pb.exists():raise SystemExit('Incomplete lifecycle captures: '+a+' / '+b)
    ia,ib=[np.asarray(Image.open(p)).astype(np.int16)for p in [pa,pb]]
    assert ia.shape==ib.shape
    diff=np.abs(ia-ib);ys,xs=np.where(diff.max(axis=2)>0)
    rows.append({'before':a,'after':b,'changedPixels':len(xs),'maxChannelDelta':int(diff.max()),
                 'bounds':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]if len(xs)else None,
                 'beforeSha256':hashlib.sha256(pa.read_bytes()).hexdigest(),'afterSha256':hashlib.sha256(pb.read_bytes()).hexdigest()})
result={'method':'Whole unmodified PNGs: requested Light view on/off pairs, winter and summer on/off and repeat/restoration pairs, and initial versus restored summer canvas.','pairs':rows,'complete':True,'allExact':all(r['changedPixels']==0 for r in rows)}
(root/'pixel-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
if not result['allExact']:raise SystemExit(1)
