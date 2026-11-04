"""Fresh native source/static proof via the unchanged20-face14/7mm policy.

No browser/native129 replay occurs here; its exact-source receipts are validated
separately. No fictitious crossing ancestry or new collision exemption is added.
"""
import json,time
import upper_orbital_source as child
import socket_qualification as original
import socket_geometry as g

def run(out):
    started=time.monotonic();source=child.Sources();structure=source.full_frozen_structure();source.cheap_tables()
    components=original.components(source,source.eye);allowed,ledger=original.source_interface_faces(source,components)
    for side,c in components.items():g.need(not original.proper_pairs(c.triangles,set(range(len(c.triangles))),source.crosses),'source_globe_self_intersection',side)
    allcontacts=original.globe_pairs(source.old_body,set(range(len(source.old_body))),source.eye,source.crosses);contactfaces={j for i,j in allcontacts}
    rest=original.evaluate_frame(source,source.body,source.old_body,source.eye,source.eye,allowed,{'kind':'rest'},contactfaces)
    source.unchanged();result={'status':'CURRENT_E49B_NATIVE_SOURCE_STATIC_ONLY_PASS','source_admission':child.MODE,'collision_policy':original.s.MODE,'candidate_sha256':child.generator.CANDIDATE_SHA,'structure':structure,'source_interface_faces':{str(k):sorted(v)for k,v in allowed.items()},'rest':rest,'seconds':time.monotonic()-started,'native129_rerun':False,'photographic_acceptance':False,'whole_app_acceptance':False}
    if out is not None:out.write_text(json.dumps(result,indent=2)+'\n')
    return result
