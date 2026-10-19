#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
import copy,json,pathlib,struct,unittest,os
from human_skin_canonicalize import read_glb,encode,consolidate,diagnostics
FIXTURE=pathlib.Path(os.environ.get('TEST_HUMAN_FIXTURE',pathlib.Path(__file__).resolve().parents[1]/'assets/humans/c4d_fixture.lod0.glb'))
def duplicate_fixture():
    doc,tail=read_glb(FIXTURE.read_bytes());doc['skins'].append(copy.deepcopy(doc['skins'][0]))
    index,node=next((i,n) for i,n in enumerate(doc['nodes']) if 'mesh'in n)
    duplicate=copy.deepcopy(node);duplicate['name']='test_duplicate_component';duplicate['skin']=1;doc['nodes'].append(duplicate)
    parent=next((n for n in doc['nodes'] if index in n.get('children',[])),None)
    if parent:parent['children'].append(len(doc['nodes'])-1)
    else:doc['scenes'][doc.get('scene',0)]['nodes'].append(len(doc['nodes'])-1)
    return encode(doc,tail)
def different_ibm(raw):
    doc,tail=read_glb(raw);binary=bytearray(tail[8:]);a=copy.deepcopy(doc['accessors'][doc['skins'][1]['inverseBindMatrices']]);v=doc['bufferViews'][a['bufferView']];offset=v.get('byteOffset',0)+a.get('byteOffset',0);data=bytearray(binary[offset:offset+a['count']*64]);struct.pack_into('<f',data,0,.99)
    doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data)});binary+=data;a['bufferView']=len(doc['bufferViews'])-1;a.pop('byteOffset',None);doc['accessors'].append(a);doc['skins'][1]['inverseBindMatrices']=len(doc['accessors'])-1;doc['buffers'][0]['byteLength']=len(binary)
    return encode(doc,struct.pack('<II',len(binary),0x004e4942)+binary)
class EquivalentSkinTest(unittest.TestCase):
 def setUp(self):self.raw=duplicate_fixture()
 def test_identical_palettes_remap_without_binary_change(self):
  result,report=consolidate(self.raw);before,binbefore=read_glb(self.raw);after,binafter=read_glb(result)
  self.assertEqual((report['input_skin_count'],report['output_skin_count']),(2,1));self.assertEqual(binbefore,binafter)
  for node in after['nodes']:
   if 'skin'in node:self.assertEqual(node['skin'],0)
  self.assertEqual(before['meshes'],after['meshes']);self.assertEqual(before['animations'],after['animations']);self.assertEqual(before['accessors'],after['accessors'])
 def test_equal_ibms_in_distinct_accessors_are_equal(self):
  d,b=read_glb(self.raw);d['accessors'].append(copy.deepcopy(d['accessors'][d['skins'][1]['inverseBindMatrices']]));d['skins'][1]['inverseBindMatrices']=len(d['accessors'])-1
  self.assertEqual(consolidate(encode(d,b))[1]['output_skin_count'],1)
 def test_reordered_joint_palette_refused(self):
  d,b=read_glb(self.raw);d['skins'][1]['joints'][1:3]=reversed(d['skins'][1]['joints'][1:3])
  with self.assertRaisesRegex(ValueError,'distinct skin palettes'):consolidate(encode(d,b))
 def test_same_names_different_actual_nodes_refused(self):
  d,b=read_glb(self.raw);d['nodes'].append(copy.deepcopy(d['nodes'][d['skins'][1]['joints'][0]]));d['skins'][1]['joints'][0]=len(d['nodes'])-1
  with self.assertRaisesRegex(ValueError,'distinct skin palettes'):consolidate(encode(d,b))
 def test_different_actual_ibms_refused(self):
  with self.assertRaisesRegex(ValueError,'distinct skin palettes'):consolidate(different_ibm(self.raw))
 def test_differing_skin_properties_refused(self):
  d,b=read_glb(self.raw);d['skins'][1]['extras']={'different_authority':True}
  with self.assertRaisesRegex(ValueError,'distinct skin palettes'):consolidate(encode(d,b))
 def test_group_mode_never_merges_distinct_palettes(self):
  result,report=consolidate(different_ibm(self.raw),require_single_skin=False);self.assertEqual(report['output_skin_count'],2)
 def test_scale_diagnostic_records_but_does_not_fix(self):
  d,b=read_glb(self.raw);i=next(i for i,n in enumerate(d['nodes']) if n.get('name')=='thigh_l');d['nodes'][i]['scale']=[1,1,.9999979734420776];raw=encode(d,b);result,_=consolidate(raw)
  self.assertGreater(diagnostics(result)['maximum_unit_scale_residual'],1e-6);self.assertEqual(read_glb(result)[0]['nodes'][i]['scale'],d['nodes'][i]['scale'])
 def test_unsupported_or_invalid_ibm_encodings_refused(self):
  for case in ['accessor_extension','view_extension','external_buffer','negative_accessor','negative_offset','boolean_joint']:
   with self.subTest(case=case):
    d,b=read_glb(self.raw);s=d['skins'][0];a=d['accessors'][s['inverseBindMatrices']];v=d['bufferViews'][a['bufferView']]
    if case=='accessor_extension':a['extensions']={'EXT_unknown':{}}
    elif case=='view_extension':v['extensions']={'EXT_meshopt_compression':{}}
    elif case=='external_buffer':d['buffers'][0]['uri']='external.bin'
    elif case=='negative_accessor':s['inverseBindMatrices']=-1
    elif case=='negative_offset':a['byteOffset']=-4
    else:s['joints'][0]=True
    with self.assertRaises(ValueError):consolidate(encode(d,b))
if __name__=='__main__':unittest.main()
