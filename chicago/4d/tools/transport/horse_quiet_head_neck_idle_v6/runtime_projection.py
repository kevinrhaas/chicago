"""PROPOSED one-quiet-clip runtime projection; no failed17 fallback/export."""
import copy
import generate_quiet_head_neck_v6 as source
MASTER_SHA='0a93029a951c000771c9fc8ca39809fd5323633b2e70fc462ba27b7ab9ccfc5b'
NOTICE='chicago4d_quiet_head_neck_runtime_v6'

def project(master):
    source.need(source.sha(master)==MASTER_SHA,'exact V6 authored master')
    doc,binary=source.read(master);quiet=[a for a in doc['animations'] if a['name']==source.NAME]
    source.need(len(quiet)==1 and len(quiet[0]['channels'])==len(quiet[0]['samplers'])==15,'one uniquely named quiet15 source clip')
    out=copy.deepcopy(doc);out['animations']=quiet
    out['asset']['extras'][NOTICE]=dict(authored_master_sha256=MASTER_SHA,selected_clip=source.NAME,exported_clips=1,unqualified17_exported=False,all_BIN_and_original_geometry_exact=True,qualification='UNRUN',runtime_adoption=False)
    result=source.write(out,binary)
    source.need(len(result)<=4*1024**2,'unchanged fourMiB runtime budget')
    inspect(master,result)
    return result

def inspect(master,runtime):
    md,mb=source.read(master);rd,rb=source.read(runtime);clean=copy.deepcopy(rd)
    notice=clean['asset']['extras'].pop(NOTICE)
    source.need(notice==dict(authored_master_sha256=MASTER_SHA,selected_clip=source.NAME,exported_clips=1,unqualified17_exported=False,all_BIN_and_original_geometry_exact=True,qualification='UNRUN',runtime_adoption=False),'exact runtime export lineage and unqualified status')
    source.need(len(clean['animations'])==1 and clean['animations'][0]==md['animations'][2] and clean['animations'][0]['name']==source.NAME,'only exact quiet15 clip, no old13/failed17 fallback')
    clean['animations']=copy.deepcopy(md['animations'])
    source.need(clean==md and rb==mb,'complete geometry/material/rig/BIN identity and explicit animation-only projection')
    source.need(source.write(clean,rb)==master,'independent reversal recovers entire exact authored master')
    return dict(original_master_sha256=source.sha(master),runtime_sha256=source.sha(runtime),runtime_bytes=len(runtime),geometry_and_BIN_exact=True,selected_clip=source.NAME,exported_clip_count=1,all_retained_curves_exact=True,master_reversal_exact=True,native_runtime_parity='UNRUN',native925_posed='UNRUN',world='UNRUN',runtime_adoption=False)
