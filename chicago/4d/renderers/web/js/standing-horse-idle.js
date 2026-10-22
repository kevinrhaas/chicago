// SPDX-License-Identifier: GPL-3.0-or-later
// SOURCE PROPOSAL: playback of an explicit exported glTF idle; no curve invention in renderer.
const ORIGINAL='41acd9bee7bf05fbcdd813fad965027b01b8801d6a21ca1c22eb2178c8842988';
const NORMALIZED='ceefa279b1602b97eac707cec19b2fbbb25c4442788981d82b20ac99ca205afc',BUNDLE='a759bf114a84a94f067fc50003473527677082dd6a4c6337bdff39babc7e73ba',NORMALIZATION_RECEIPT='7b7c75927a760e08b8d1ebce56ac6fb3081460b96e3c22811afb6bffd1714329';
const CLIP='sevket_reconstructed_head_tail_idle_v1',OWNER=Symbol('sourceBoundIdle');
const EXPECTED=[{"role":"head","native_node_index":17,"skin_joint_index":12,"native_node_name":"Bone.011_Armature","native_default_quaternion_xyzw":[0.6245548725128174,-0.03226621821522713,-0.050310324877500534,0.7786905169487]},{"role":"tail","native_node_index":19,"skin_joint_index":14,"native_node_name":"Bone.013_Armature","native_default_quaternion_xyzw":[0.8690532445907593,-0.0966569036245346,0.3291347920894623,0.35647469758987427]}];
const HOOFS=['fore_l','fore_r','hind_l','hind_r'];
const check=(ok,msg)=>{if(!ok)throw Error('HorseIdleContract: '+msg);};
function stableHash(text){let h=2166136261;for(const c of text){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return h>>>0;}
export function createExportedHorseIdle({T,root,clips,verifiedDerivedSha256,appendReceipt,source,instanceId}){
 check(source?.source_sha256===ORIGINAL,'source identity mismatched');
 check(Array.isArray(source.derived_channels)&&source.derived_channels.length===2,'exact two source channels required');
 for(const expected of EXPECTED){const matches=source.derived_channels.filter(c=>c.skin_joint_index===expected.skin_joint_index);check(matches.length===1,'source channel cardinality changed');const c=matches[0];for(const k of ['role','native_node_index','native_node_name'])check(c[k]===expected[k],'source channel identity changed');check(Array.isArray(c.native_default_quaternion_xyzw)&&c.native_default_quaternion_xyzw.length===4&&c.native_default_quaternion_xyzw.every((v,i)=>v===expected.native_default_quaternion_xyzw[i]),'source rest quaternion changed');}
 check(typeof verifiedDerivedSha256==='string'&&/^[a-f0-9]{64}$/.test(verifiedDerivedSha256),'actual derived SHA required');
 check(appendReceipt?.schema==='sevket_normalized_lineage_idle_append_v1'&&appendReceipt.normalized_input_sha256===NORMALIZED&&appendReceipt.upstream_original_sha256===ORIGINAL&&appendReceipt.derived_sha256===verifiedDerivedSha256,'actual normalized-lineage derived byte proof mismatched');
 check(appendReceipt.normalization_receipt_sha256===NORMALIZATION_RECEIPT&&appendReceipt.bundle_sha256===BUNDLE,'normalization/curve identity changed');
 check(typeof appendReceipt.normalization_parity_receipt_sha256==='string'&&/^[a-f0-9]{64}$/.test(appendReceipt.normalization_parity_receipt_sha256),'actual normalization parity receipt missing');
 check(appendReceipt.normalized_buffer_prefix_exact===true&&appendReceipt.every_normalized_buffer_view_exact===true&&appendReceipt.normalized_nodes_skins_meshes_materials_images_asset_exact===true&&appendReceipt.normalized_accessors_and_six_animations_exact===true&&appendReceipt.normalized_input_unchanged_after===true,'normalized protection proof missing');
 const exceptions=appendReceipt.normalization_exceptions;check(exceptions?.old_animation_accessors_repacked_reference_only===true&&exceptions.exact_zero_weight_joint_components_zeroed===15897&&exceptions.mesh_nodes_21_22_23_promoted_with_identity_local_transform===true&&exceptions.original_six_decoded_animation_keys_exact===true&&exceptions.mesh_basis_change_parity_receipt_sha256===appendReceipt.normalization_parity_receipt_sha256,'normalization exceptions/proof changed');
 check(typeof instanceId==='string'&&instanceId.length>0,'stable instance identity required');
 check(!root.userData[OWNER],'another source idle owns this clone');
 const meshes=[];root.traverse(n=>{if(n.isMesh)meshes.push(n);});check(meshes.length===3&&meshes.every(m=>m.isSkinnedMesh&&m.skeleton.bones.length===15),'source skin inventory changed');
 const bones=meshes[0].skeleton.bones;check(meshes.every(m=>m.skeleton.bones.every((b,i)=>b===bones[i])),'source joint identity/order changed');
 for(const c of EXPECTED)check(bones[c.skin_joint_index].name===T.PropertyBinding.sanitizeNodeName(c.native_node_name)&&bones[c.skin_joint_index].userData.name===c.native_node_name,'source leaf name/order changed');
 const clip=clips.find(c=>c.name===CLIP);check(clips.length===7&&clips.filter(c=>c.name===CLIP).length===1&&clip.duration===12&&clip.tracks.length===2,'explicit exported idle missing/changed');
 const targets=new Set();for(const track of clip.tracks){const p=T.PropertyBinding.parseTrackName(track.name);check(p.propertyName==='quaternion','only quaternion tracks permitted');const node=T.PropertyBinding.findNode(root,p.nodeName);check(node===bones[12]||node===bones[14],'unapproved bone track');check(!node.children.some(n=>n.isBone),'idle target no longer a leaf');targets.add(node);}check(targets.size===2,'head/tail leaves must each occur once');
 check(source.support_guard?.mesh_renderer_name==='BezierCurve005_Mesh005_1'&&source.support_guard.vertex_count===4313,'source contact identity changed');
 const body=root.getObjectByName(source.support_guard.mesh_renderer_name),idx=body?.geometry.index,pos=body?.geometry.getAttribute('position'),ji=body?.geometry.getAttribute('skinIndex'),sw=body?.geometry.getAttribute('skinWeight');check(body?.isSkinnedMesh&&idx&&pos&&ji&&sw,'source contact body missing');
 check(pos.count===4313&&ji.count===pos.count&&sw.count===pos.count&&ji.itemSize===4&&sw.itemSize===4&&idx.count%3===0,'source attribute dimensions changed');
 const patches=source.support_guard.triangles_by_hoof;check(patches&&Object.keys(patches).length===4&&HOOFS.every(k=>Object.hasOwn(patches,k)),'exact four hoof patches required');
 const ids=new Set();for(const name of HOOFS){const faces=patches[name];check(Array.isArray(faces)&&faces.length>0,'nonempty hoof patch required');for(const face of faces){check(Number.isInteger(face)&&face>=0&&face<idx.count/3,'hoof triangle out of bounds');for(let k=0;k<3;k++){const id=idx.getX(face*3+k);check(Number.isInteger(id)&&id>=0&&id<pos.count,'hoof vertex out of bounds');ids.add(id);}}}
 for(const id of ids)for(const axis of ['X','Y','Z','W'])if([12,14].includes(ji['get'+axis](id)))check(sw['get'+axis](id)===0,'idle leaf influences annotated hoof surface');
 // Caller must construct at exact rest and own all animation clocks for this clone.
 for(const c of source.derived_channels){const q=bones[c.skin_joint_index].quaternion;check(Number.isFinite(q.length())&&Math.abs(q.length()-1)<1e-5&&q.clone().normalize().angleTo(new T.Quaternion().fromArray(c.native_default_quaternion_xyzw).normalize())<1e-5,'actor not in source rest pose');}
 const mixer=new T.AnimationMixer(root),action=mixer.clipAction(clip);action.setLoop(T.LoopRepeat,Infinity);action.play();mixer.setTime(0);root.userData[OWNER]=true;
 const initialRestDelay=2*(stableHash(instanceId)/4294967295),rate=.96+.08*(stableHash(instanceId+'|rate')/4294967295);
 let disposed=false,elapsed=0,age=0;
 return{update(dt,{visible=true,reducedMotion=false,paused=false}={}){if(disposed)return;check(Number.isFinite(dt)&&dt>=0,'invalid clock');if(!visible||reducedMotion||paused)return;const step=dt,before=age;age+=step;const advance=(Math.max(0,age-initialRestDelay)-Math.max(0,before-initialRestDelay))*rate;elapsed+=advance;mixer.update(advance);},
  get status(){return{elapsed_s:elapsed,disposed,clip:CLIP,initial_rest_delay_s:initialRestDelay,deterministic_playback_rate:rate,clock_contract:'visible/unpaused host delta; no adapter clamp; seed determines delay/rate, not wall-clock time',mixer_count:disposed?0:1,weight_shift:false,independent_ear_motion:false,walk:false,trot:false};},
  // Host removes/hides the clone before retiring its player, avoiding visible reset on teardown.
  dispose(){if(disposed)return;disposed=true;mixer.stopAllAction();mixer.uncacheRoot(root);delete root.userData[OWNER];},
 };
}
