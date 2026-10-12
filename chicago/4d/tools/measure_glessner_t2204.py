"""Compare the native-resolution, matched moving roof samples from qa_glessner_t2204.mjs.
The red-clay mask excludes UI, sky, stone and moving roof boundaries. Differences
are observations of these paths, not a general temporal-AA or hardware FPS claim.
"""
import argparse,json,shutil,statistics
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_erosion
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
p.add_argument('--pullback',type=Path)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
reports=[]
for label in ('desktop','mobile'):
    for view in ('near','street','overhead','northeast'):
        images=[[Image.open(folder/f'{label}-{view}-{i}.png').convert('RGB') for i in range(6)] for folder in (a.before,a.after)]
        arrays=[np.stack([np.asarray(im,dtype=float) for im in seq]) for seq in images]
        masks=[]
        for seq in arrays:
            red,green,blue=seq[...,0],seq[...,1],seq[...,2]
            masks.append(np.all((red>1.4*green)&(green>1.05*blue)&(red>35),axis=0))
        mask=binary_erosion(masks[0]&masks[1],iterations=2)
        mask[:220 if label=='desktop' else 190]=False
        assert mask.sum()>40,(label,view,'insufficient stable roof pixels')
        values=[]
        for seq in arrays:
            luma=seq@np.array([.2126,.7152,.0722]);d=np.abs(np.diff(luma,axis=0))[:,mask]
            values.append({'mean_luma_change_255':float(d.mean()),'p95_luma_change_255':float(np.percentile(d,95)),
                           'changes_over_12_fraction':float(np.mean(d>12)),'samples':int(d.size)})
        reports.append({'viewport':label,'path':view,'stable_roof_pixels':int(mask.sum()),'before':values[0],'after':values[1]})
        for phase,seq in zip(('before','after'),images):
            shutil.copyfile((a.before if phase=='before' else a.after)/f'{label}-{view}-0.png',a.output/f'{phase}-{label}-{view}.png')
        y,x=np.where(masks[0]|masks[1]);box=(max(0,int(x.min())-8),max(190,int(y.min())-8),min(images[0][0].width,int(x.max())+9),min(images[0][0].height,int(y.max())+9))
        panels=[]
        for left,right in zip(*images):
            left,right=left.crop(box),right.crop(box)
            scale=min(1,620/left.width);size=(round(left.width*scale),round(left.height*scale))
            panel=Image.new('RGB',(size[0]*2,size[1]+24),'white');panel.paste(left.resize(size),(0,24));panel.paste(right.resize(size),(size[0],24))
            draw=ImageDraw.Draw(panel);draw.text((8,5),f'Before / {label} / {view}',fill='black');draw.text((size[0]+8,5),'After / same moving camera',fill='black');panels.append(panel)
        palette=panels[0].quantize(colors=256,dither=Image.Dither.NONE)
        panels=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in panels]
        panels[0].save(a.output/f'motion-{label}-{view}.gif',save_all=True,append_images=panels[1:]+panels[-2:0:-1],duration=250,loop=0)
costs=[]
for phase,folder in [('before',a.before),('after',a.after)]:
    receipts=list(folder.glob('browser-validation*.json'))
    for receipt in receipts:
        for row in json.loads(receipt.read_text())['results']:
            frames=[v for v in row['stands'] if not v['name'].startswith('pullback-')];warmed=[v['frameMs'] for v in frames if not v['name'].endswith('-0')]
            costs.append({'phase':phase,'viewport':row['label'],'detail':row['detail'],'median_render_submission_and_finish_call_ms':statistics.median(warmed),
                          'draw_calls':sorted(set(v['stats']['drawCalls'] for v in frames)),
                          'triangles':sorted(set(v['stats']['triangles'] for v in frames)),
                          'textures':sorted(set(v['stats']['textures'] for v in frames)),
                          'filter_attribute_bytes':sorted(set(v.get('filterBytes',0) for v in frames))})
(a.output/'motion-and-costs.json').write_text(json.dumps({'method':__doc__,'cost_limit':'These frameMs values time submission and a WebGL finish call, which did not block for GPU completion on this runner. Use the separate readPixels benchmark for frame cost. Baseline also overlapped the bake. No speedup or hardware FPS claim.','paths':reports,'costs':costs},indent=2)+'\n')
print(json.dumps(reports,indent=2))

if a.pullback:
    receipt=json.loads((a.pullback/'browser-validation.json').read_text())
    shutil.copyfile(a.pullback/'browser-validation.json',a.output/'pullback-and-gpu-cost.json')
    for row in receipt['results']:
        sheet=Image.new('RGB',(960,4*224),'white');draw=ImageDraw.Draw(sheet)
        for index,stand in enumerate(v for v in row['stands'] if v['name'].startswith('pullback-')):
            source=a.pullback/f"{row['label']}-{stand['name']}.png"
            im=Image.open(source).convert('RGB');im.thumbnail((320,200))
            x=(index%3)*320;y=(index//3)*224
            draw.text((x+5,y+4),stand['name'].replace('pullback-','').removesuffix('-0')+' m',fill='black')
            sheet.paste(im,(x,y+24))
            if stand['name'] in ('pullback-7-0','pullback-12-0','pullback-32-0'):
                shutil.copyfile(source,a.output/source.name)
        sheet.save(a.output/f"pullback-{row['label']}.png")
