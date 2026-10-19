#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Anonymous roles must not create resident identities or cross wardrobe/date bounds."""
import copy
from human_contract import check_instance, load_json, CONTRACT, SCHEMA, role_profiles
c=load_json(CONTRACT);schema=load_json(SCHEMA)
profile=copy.deepcopy(role_profiles()['anonymous_adult_1835'])
profile['eligible_assets']=[{'asset_id':'c4d_fixture','period':{'earliest_year':1835,'latest_year':1835},'wardrobe_basis':'Synthetic unpublished test qualification only; not a production outfit acceptance.'}]
base={'id':'hi_anonymous_driver_01','contract_version':1,'scene':'1835','anonymous_profile_id':profile['id'],'role':'driver','fallback_basis':'Synthetic test: no historical candidate is selected in this unpublished mechanical fixture.','considered_person_ids':[],'appearance':{'asset_id':'c4d_fixture'},'placement':{'local_e':0,'local_n':0,'heading_deg':0,'anchor':'terrain'},'animation':{'clip':'idle'},'behaviour':{'state':'seated'},'interaction':{'selectable':True,'opens':'role_card'},'lod':{'policy':'auto'},'display':'shown','review_required':False,'provenance':{'grade':'reconstructed','basis':'Synthetic adult role fixture, never a historical individual.','liberty':'L418'}}
def codes(r,ctx=None):return {f.code for f in check_instance(r,c,schema,ctx=ctx if ctx is not None else {'profiles':{profile['id']:profile}})}
assert not codes(base),codes(base)
for title,change,code in [
 ('wrong profile date',{'scene':'1904'},'instance.profile_date'),
 ('no made-up person',{'person_id':'invented_driver'},'instance.schema'),
 ('no resident card',{'interaction':{'selectable':True,'opens':'resident_card'}},'instance.schema'),
 ('no unsupported role',{'role':'mayor'},'instance.schema'),
 ('no unaccepted wardrobe',{'appearance':{'asset_id':'worker_1904'}},'instance.profile_asset'),
 ('no unsupported fallback',{'fallback_basis':'use generic'},'instance.schema'),
 ('no fake considered person',{'considered_person_ids':['invented_candidate']},'instance.fallback_person'),
 ('no attested anonymous identity',{'provenance':{**base['provenance'],'grade':'attested'}},'instance.schema'),
]:
 result=codes({**base,**change});assert code in result,(title,result)
ctx={'profiles':{profile['id']:profile}}
assert not codes(base,ctx)
assert 'instance.duplicate_id' in codes(base,ctx)
assert not codes({**base,'id':'hi_anonymous_driver_02'},ctx),'a shared profile is not one shared person'
wrong_wardrobe=copy.deepcopy(profile);wrong_wardrobe['eligible_assets'][0]['period']={'earliest_year':1904,'latest_year':1904}
assert 'instance.profile_asset' in codes(base,{'profiles':{profile['id']:wrong_wardrobe}})
assert 'instance.profile_asset' in codes(base,{'profiles':role_profiles()}),'committed empty eligibility must refuse placeholders'
print('anonymous Python schema/semantic refusal checks passed')
