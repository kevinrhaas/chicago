#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Register and build the existing people's portrait photographs: --all; inspect: --check.

Original identity/crop/rights records remain authoritative. Existing four-view skin
sheets are retained. Stand-ins keep their explicit labels and reconstructed grade.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import date

from PIL import Image, ImageOps
import photo_face_library as P

ROOT=P.ROOT
RECIPE=ROOT/'data/humans/variation/historical_photo_faces.json'
AUTHORED=ROOT/'assets/authored/humans/historical_photo_faces'
OUTPUT=ROOT/'assets/humans/web/photo_faces/historical'
REFERENCES=ROOT/'data/humans/variation/person_photo_references.json'


def write_json(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    encoded=json.dumps(data,indent=1,ensure_ascii=False)+'\n'
    if not path.exists() or path.read_text()!=encoded:path.write_text(encoded)


def inventory():
    people=json.loads((ROOT/'assets/humans/web/hm08_variation_persons.json').read_text())['persons']
    rows=[]
    for path in sorted(P.F.PORTRAITS.glob('*.json')):
        portrait=json.loads(path.read_text());person=path.stem
        if person not in people:continue
        record=people[person]
        source=json.loads((ROOT/'data/sources'/f"{portrait['source']}.json").read_text())
        image=ROOT/portrait['card']['portrait']
        rows.append({'person':person,'record':record,'portrait':portrait,'source':source,'image':image,
                     'status':'existing_skin' if record.get('skin') else 'labelled_stand_in' if portrait.get('stand_in') else 'own_portrait'})
    return rows


def register(model):
    rows=inventory();pending=[r for r in rows if r['status']!='existing_skin']
    texture_source='historical_photo_textures_3762';P.source_record(texture_source)
    states=json.loads(subprocess.check_output(['node',str(ROOT/'tools/historical_photo_state.mjs'),*[r['person'] for r in pending]],cwd=ROOT,text=True))
    previous=json.loads(RECIPE.read_text()) if RECIPE.exists() else {'faces':[]}
    old={e['id']:e for e in previous['faces']}
    source_path=AUTHORED/'SOURCE.json'
    lineage=json.loads(source_path.read_text()) if source_path.exists() else {'processed':[]}
    processed={r['person_id']:r for r in lineage['processed']}
    entries=[]
    for row in pending:
        person,portrait,source,state=row['person'],row['portrait'],row['source'],states[row['person']]
        if source['rights_status'] not in ['public_domain','no_known_restrictions']:
            raise ValueError(person+': original portrait rights are not cleared for reuse')
        if not row['image'].exists():raise ValueError(person+': registered portrait image is missing')
        e=old.get(person)
        if e is None:
            # The retained card image already carries the existing crop/identity reading.
            im=ImageOps.grayscale(Image.open(row['image'])).convert('RGB')
            points=P.detect(im,model)
            outline=[points[i] for i in [10,234,454,152,127,356]]
            xs,ys=zip(*outline);width,height=max(xs)-min(xs),max(ys)-min(ys)
            size=max(width*1.55,height*1.5);cx=(max(xs)+min(xs))/2;cy=(max(ys)+min(ys))/2-height*.1
            box=[max(0,int(cx-size/2)),max(0,int(cy-size/2)),min(im.width,int(cx+size/2)+1),min(im.height,int(cy+size/2)+1)]
            im=im.crop(box)
            points=[[round(x-box[0],4),round(y-box[1],4)] for x,y in points]
            photo=AUTHORED/f'{person}.png';photo.parent.mkdir(parents=True,exist_ok=True);im.save(photo)
            sid=texture_source
            note='Reuses the existing credited portrait crop; no facial detail is generated. The source is monochrome and does not attest colour.'
            e={'id':person,'source':sid,'photo':P.relative(photo),'photo_sha256':P.digest(photo),
               'age':portrait['age_at_picture_years'],'sex':state['sex'],'synthetic':False,'landmarks':points,
               'shape_from':f'data/humans/variation/fits/{person}.json','reference_source':portrait['source']}
            processed[person]={'person_id':person,'input_file':str(row['image'].relative_to(ROOT)),
                'input_sha256':P.digest(row['image']),'input_url':'https://raw.githubusercontent.com/kevinrhaas/chicago/b7938d0d758f504aeaa1d32e6f4082409955b310/chicago/4d/'+str(row['image'].relative_to(ROOT)),
                'grayscale':True,'crop_of_retained_portrait':box,'processed_file':e['photo'],'processed_sha256':e['photo_sha256'],'note':note}
        label=state['label']
        if portrait.get('stand_in'):label+=' · '+portrait['stand_in']['label']
        e.update(source=texture_source,label=label,historical={'person_id':person,'scene':str(row['record']['scene']),
            'active_cast':bool(state['drawn_as']),'identity_basis':row['status'],'stand_in':portrait.get('stand_in'),'monochrome':True,
            'scene_age':state['age'],'reference_asset':state['asset'],'before_values':state['values'],
            'before_height':state['height'],'before_hair_rgb':state['hair_rgb'],
            'original_source':portrait['source'],'source_publication_date':source.get('date'),
            'source_describes_date':source.get('describes_date'),'photo_age_basis':portrait.get('age_note'),
            'limits':['Monochrome photographs do not attest skin, iris or hair colour; existing chosen colours are retained.',
                      'Exposure and publication dates may differ; scene age and presence remain the population record’s.',
                      'Unseen profile depth and features remain reconstructed.',
                      *([portrait['stand_in']['card_note']] if portrait.get('stand_in') else [])]})
        entries.append(e)
    refs=json.loads(REFERENCES.read_text())['people'] if REFERENCES.exists() else []
    if refs:
        snapshots=json.loads(subprocess.check_output(['node',str(ROOT/'tools/historical_photo_state.mjs'),*[r['person_id'] for r in refs]],cwd=ROOT,text=True))
        for ref in refs:
            person=ref['person_id'];state=snapshots[person]
            if any(e['id']==person for e in entries):raise ValueError(person+': reference would replace an existing curated portrait')
            P.source_record(ref['source'])
            if state['age']<18:raise ValueError('Named juvenile references require the separate child texture-only path')
            e=old.get(person,{})
            if e.get('photo_sha256') and P.digest(ROOT/ref['photo'])!=e['photo_sha256']:raise ValueError(person+': source photo changed; explicitly register the replacement')
            e.update(id=person,label=ref.get('label',state['label'])+' · '+ref['stand_in']['label'],source=ref['source'],photo=ref['photo'],
                     photo_sha256=P.digest(ROOT/ref['photo']),sex=state['sex'],age=ref['age'],synthetic=False,
                     **({'crop_px':ref['crop_px']} if ref.get('crop_px') else {}),
                     historical={'person_id':person,'scene':'1904','identity_basis':'labelled_stand_in','stand_in':ref['stand_in'],
                        'active_cast':bool(state['drawn_as']),'shape_mode':'new_photo_fit','monochrome':ref.get('monochrome',False),'scene_age':state['age'],
                        'reference_asset':state['asset'],'before_values':state['values'],'before_height':state['height'],
                        'before_hair_rgb':state['hair_rgb'],'original_source':ref['source'],
                        'reference':ref.get('reference',ref['photo']),'reference_crop_px':ref.get('reference_crop_px'),
                        **{k:ref[k] for k in ['hair_style','spectacles','iris_rgb_linear','fit_controls'] if k in ref},
                        'limits':[ref['stand_in']['card_note'],'Only one photographic view was supplied; hidden profile depth is reconstructed.',
                                  'Period hair/clothes, neutral expression and removed spectacles in the texture companion are edited, not historical evidence.']})
            entries.append(e)
            rows.append({'person':person,'status':'labelled_stand_in','portrait':{'source':ref['source']},'image':ROOT/ref.get('reference',ref['photo']),'cast':bool(state['drawn_as'])})
    recipe={'frontal':False,'activation':{'tier':'dev','requested_by':'owner','years':['1812','1835','1871','1904'],
             'request':'Apply all existing person photographs to their matching people; keep explicit stand-in labels.'},'faces':entries}
    write_json(RECIPE,recipe)
    write_json(source_path,{'not_a_reading':'Reuse of previously identified portrait photographs and explicitly labelled stand-ins; no new person identification.',
                           'ticket':'T-3762','processed':[processed[k] for k in sorted(processed)]})
    return recipe,rows


def build(model,jobs):
    recipe,rows=register(model)
    result=P.build(recipe,OUTPUT,model,jobs=jobs)
    # Preserve freshly registered camera/landmark caches in the authored recipe.
    write_json(RECIPE,json.loads((OUTPUT/'recipe.json').read_text()))
    coverage=[{'person':r['person'],'status':r['status'],'source':r['portrait']['source'],
               'portrait':str(r['image'].relative_to(ROOT)),'active_cast':r.get('cast',bool(r.get('record',{}).get('drawn_as')))} for r in rows]
    write_json(OUTPUT/'coverage.json',{'ticket':'T-3762','people':coverage})
    for ref in json.loads(REFERENCES.read_text()).get('people',[]):
        image=P.read_photo(ROOT/ref.get('reference',ref['photo']),ref.get('reference_crop_px',ref.get('crop_px')))
        image.thumbnail((480,640),Image.Resampling.LANCZOS)
        image.save(OUTPUT/(ref['person_id']+'_reference.jpg'),quality=93,subsampling=0,optimize=True)
    return result


def check():
    P.check(OUTPUT/'review.json')
    lib=json.loads((OUTPUT/'review.json').read_text());rows=inventory()
    wanted={r['person'] for r in rows if r['status']!='existing_skin'}
    wanted.update(r['person_id'] for r in json.loads(REFERENCES.read_text()).get('people',[]))
    assert {f['id'] for f in lib['faces']}==wanted,'every registered untextured portrait has its own binding'
    assert max(lib['textures']['light']['size_px'])<=256,'personal crowd sheet stays within 256 pixels'
    for face in lib['faces']:
        h=face['historical']
        if face.get('shape_from'):assert face['texture_only'] and face['values']==h['before_values']
        else:assert not face['texture_only'] and h['shape_mode']=='new_photo_fit'
        assert h['person_id']==face['id'] and h['identity_basis'] in ['own_portrait','labelled_stand_in']
        if h['identity_basis']=='labelled_stand_in':assert h['stand_in']['label'] in face['label']
    print(f"PASS: {len(lib['faces'])} exact portrait bindings; existing skin sheets and stand-in identities preserved")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--all',action='store_true');ap.add_argument('--check',action='store_true')
    ap.add_argument('--person',help='existing person id for one new owner-chosen reference')
    ap.add_argument('--photo',type=Path);ap.add_argument('--source');ap.add_argument('--age',type=int)
    ap.add_argument('--stand-in',help='required explicit label for an owner-chosen reference model')
    ap.add_argument('--model',type=Path,default=ROOT/'work/face_landmarker.task');ap.add_argument('--jobs',type=int,default=4)
    args=ap.parse_args()
    if args.check:check();return
    if args.person:
        if not all([args.photo,args.source,args.age,args.stand_in]):ap.error('--person requires --photo, --source, --age and --stand-in')
        if not args.stand_in.startswith('STAND-IN'):ap.error('--stand-in must begin STAND-IN')
        P.source_record(args.source)
        state=json.loads(subprocess.check_output(['node',str(ROOT/'tools/historical_photo_state.mjs'),args.person],cwd=ROOT,text=True))[args.person]
        if state['age']<18:ap.error('use the child texture-only importer for a juvenile')
        if not __import__('re').fullmatch(r'[a-zA-Z0-9_-]{1,96}',args.person):ap.error('invalid person id')
        P.read_photo(args.photo)
        import shutil
        target=AUTHORED/(args.person+'_reference'+args.photo.suffix.lower())
        if target.exists() and P.digest(target)!=P.digest(args.photo):ap.error('registered photo differs; review and explicitly remove the previous registration first')
        target.parent.mkdir(parents=True,exist_ok=True)
        if args.photo.resolve()!=target.resolve():shutil.copyfile(args.photo,target)
        refs=json.loads(REFERENCES.read_text())
        if any(r['person_id']==args.person for r in refs['people']):ap.error('person already has a registered reference')
        refs['people'].append({'person_id':args.person,'source':args.source,'photo':P.relative(target),'age':args.age,
          'label':state['label'],'stand_in':{'label':args.stand_in,'card_note':'Owner-selected reference model; not a verified photograph of the historical person.'},'monochrome':False})
        write_json(REFERENCES,refs)
    if not (args.all or args.person):ap.error('choose --all, --person or --check')
    build(args.model,args.jobs);check()


if __name__=='__main__':main()
