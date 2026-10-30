// SPDX-License-Identifier: GPL-3.0-or-later
// OUTSIDE PHASE-B PROPOSAL ONLY. No certificate pin has been invented/installed.
export const QUIET_MODE='quiet_head_neck_idle_v6';
export const QUIET_SHA='7ce84d43445e930eecc6d9f69e97ed7ade0fe0b3fc44a9a753c25d88b3f548e1';
export const QUIET_BYTES=4165556;
export const QUIET_MASTER_SHA='0a93029a951c000771c9fc8ca39809fd5323633b2e70fc462ba27b7ab9ccfc5b';
export const QUIET_CLIP='sevket_reconstructed_quiet_head_neck_idle_v1';
export const PLAYBACK_CONTRACT=Object.freeze({duration_s:12,maximum_initial_delay_s:2,minimum_rate:.96,maximum_rate:1.04,observation_margin_s:2});
const ROTATIONS=[2,3,7,8,9,12,13,14,17,18,19,22,23,24];
const NAMES={1:'horse_body',2:'horse_neck',3:'horse_head',7:'fore_l_elbow',8:'fore_l_carpus',9:'fore_l_fetlock',12:'fore_r_elbow',13:'fore_r_carpus',14:'fore_r_fetlock',17:'hind_l_stifle',18:'hind_l_hock',19:'hind_l_fetlock',22:'hind_r_stifle',23:'hind_r_hock',24:'hind_r_fetlock'};
const OWNER=Symbol('quietHeadNeckStandingOwner');
const check=(ok,message)=>{if(!ok)throw Error('HorseQuietHeadNeckContract: '+message);};
const hash=text=>{let h=2166136261;for(const c of text){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return h>>>0;};
export function requiredObservationSeconds(contract=PLAYBACK_CONTRACT){
 check([contract.duration_s,contract.maximum_initial_delay_s,contract.minimum_rate,contract.observation_margin_s].every(Number.isFinite)&&contract.duration_s>0&&contract.maximum_initial_delay_s>=0&&contract.minimum_rate>0&&contract.observation_margin_s>=0,'finite real observation contract');
 return Math.ceil(Math.max(16,contract.maximum_initial_delay_s+contract.duration_s/contract.minimum_rate+contract.observation_margin_s));
}
/** Inventory only. The caller separately verifies exact GLB SHA and certificate. */
export function inspectQuietStandingAsset(bytes){
 check(bytes.byteLength===QUIET_BYTES&&bytes.byteLength<=4*1024*1024,'exact quiet runtime byte budget');
 const v=new DataView(bytes);check(v.getUint32(0,true)===0x46546c67&&v.getUint32(4,true)===2&&v.getUint32(8,true)===bytes.byteLength&&v.getUint32(16,true)===0x4e4f534a,'complete glTF2 runtime');
 const n=v.getUint32(12,true);check(n>0&&n<=bytes.byteLength-20,'bounded JSON chunk');const d=JSON.parse(new TextDecoder().decode(new Uint8Array(bytes,20,n)));
 check(!d.extensionsRequired?.length&&d.buffers.length===1&&!d.buffers[0].uri&&d.images.length===6&&d.images.every(i=>Number.isInteger(i.bufferView)&&!i.uri)&&d.materials.length===3,'exact embedded runtime images/materials');
 check(d.skins.length===1&&d.skins[0].joints.length===26&&d.skins[0].joints.every((x,i)=>x===i),'source26 joint inventory');
 const note=d.asset?.extras?.chicago4d_quiet_head_neck_runtime_v6;check(note?.authored_master_sha256===QUIET_MASTER_SHA&&note.selected_clip===QUIET_CLIP&&note.exported_clips===1&&note.unqualified17_exported===false&&note.all_BIN_and_original_geometry_exact===true,'explicit onequiet runtime/master lineage');
 const binding=d.asset?.extras?.chicago4d_quiet_head_neck_idle_v6;check(binding?.binding_version===6&&binding.source_parent_sha256==='0ced8a09e27da047ad404c902e9d032e43654393027199db8dfd9c315be17929'&&binding.head_template_sha256==='a9d9573368f48b4df839c3f246035aa7ac96b04ca098c37e015113266954cf8e'&&binding.recipe_sha256==='240b6c2f83de101417301d6cd97a0c5411c6d55ad6bb12d7670dc1e8204ed213'&&binding.selected_clip===QUIET_CLIP&&binding.old_certificate_transferred===false,'exact reconstructed V6 source field/recipe, no historical proof transfer');
 check(d.animations.length===1&&d.animations[0].name===QUIET_CLIP,'only exact named quiet15, no old13/failed17 fallback');const clip=d.animations[0],targets=new Set();check(clip.channels.length===15&&clip.samplers.length===15,'exact quiet15 channel inventory');
 for(const c of clip.channels){const{node,path}=c.target,key=node+':'+path;check((node===1&&path==='translation')||(ROTATIONS.includes(node)&&path==='rotation'),'only original13 plus full neck/head targets');check(d.nodes[node].name===NAMES[node]&&!targets.has(key),'unique source joint identity');targets.add(key);const s=clip.samplers[c.sampler],input=d.accessors[s.input],output=d.accessors[s.output];check(s.interpolation==='LINEAR'&&input.componentType===5126&&input.type==='SCALAR'&&input.count===65&&input.min?.[0]===0&&input.max?.[0]===12&&output.componentType===5126&&output.count===65&&output.type===(path==='translation'?'VEC3':'VEC4'),'exact native65key LINEAR source curves');}
 check(targets.size===15&&targets.has('2:rotation')&&targets.has('3:rotation')&&!targets.has('4:rotation')&&!targets.has('5:rotation'),'quiet head/neck required, tail gesture absent');
 let triangles=0;for(const mesh of d.meshes)for(const p of mesh.primitives){check((p.mode??4)===4&&p.indices!==undefined,'indexed source mesh');triangles+=d.accessors[p.indices].count/3;}check(d.meshes.length===3&&triangles===17390,'source mesh/triangle budget');return d;
}
/**
 * Future caller supplies an actual newly executed certificateSHA pinned in
 * reviewed source AFTER canonical qualification. Never use unverified sidecar
 * data as this trusted expected pin. Positive certified tests remain UNRUN
 * until that real certificate exists; this proposal has no placeholderSHA.
 */
export function createQuietHeadNeckStandingContract({qualificationSha256}={}){
 check(typeof qualificationSha256==='string'&&/^[0-9a-f]{64}$/.test(qualificationSha256)&&qualificationSha256!=='e730f59fdbf32db6a02270b62b96c2f0d75b4f465cdbe1fda4a957cfa8530342','explicit real new certificate pin required; old bd443 proof cannot transfer');
 const validateHeader=(bytes,spec)=>{
  const r=spec.runtime_asset;check(r?.source_qualification_mode===QUIET_MODE&&r.sha256===QUIET_SHA&&r.bytes===QUIET_BYTES&&r.qualification_sha256===qualificationSha256&&r.animation_count===1&&r.declared_idle_clip===QUIET_CLIP,'exact reviewed runtime/mode/certificate/onequiet selection');
  check(spec.idle?.enabled===true&&spec.idle.clip===QUIET_CLIP&&spec.runtime_scale_m_per_unit===1&&spec.runtime_origin_m?.length===3&&spec.runtime_origin_m.every(x=>x===0),'canonical metres and explicit quiet idle');return inspectQuietStandingAsset(bytes);
 };
 const createIdle=({T,root,clips,verifiedDerivedSha256,instanceId,sourceQualificationMode})=>{
  check(sourceQualificationMode===QUIET_MODE&&verifiedDerivedSha256===QUIET_SHA&&typeof instanceId==='string'&&instanceId.length>0,'exact quiet runtime/mode/instance');check(!root.userData[OWNER],'standing clone already has quiet animation owner');
  const meshes=[];root.traverse(n=>{if(n.isMesh)meshes.push(n);});check(meshes.length===3&&meshes.every(m=>m.isSkinnedMesh&&m.skeleton.bones.length===26),'native source skin inventory');const bones=meshes[0].skeleton.bones;check(meshes.every(m=>m.skeleton.bones.every((b,i)=>b===bones[i])),'shared source bone identity/order');
  const selected=clips.filter(c=>c.name===QUIET_CLIP);check(clips.length===1&&selected.length===1,'uniquely named onequiet runtime, no fallback');const clip=selected[0];check(clip.duration===12&&clip.tracks.length===15,'native quiet12s/15track contract');const targets=new Set();
  for(const track of clip.tracks){const parsed=T.PropertyBinding.parseTrackName(track.name),node=T.PropertyBinding.findNode(root,parsed.nodeName),joint=bones.indexOf(node),key=joint+':'+parsed.propertyName;check((joint===1&&parsed.propertyName==='position')||(ROTATIONS.includes(joint)&&parsed.propertyName==='quaternion'),'only original13 plus neck/head, no procedural root/tail/gait target');check(node.name===NAMES[joint]&&!targets.has(key),'native joint identity/unique target');targets.add(key);check(track.times.length===65&&Array.from(track.times).every((x,i)=>x===i*12/64),'all real65source key times retained');}
  check(targets.has('2:quaternion')&&targets.has('3:quaternion')&&!targets.has('4:quaternion')&&!targets.has('5:quaternion'),'actual quiet head/neck inventory');
  const mixer=new T.AnimationMixer(root),action=mixer.clipAction(clip);action.setLoop(T.LoopRepeat,Infinity);action.play();mixer.setTime(0);root.userData[OWNER]=true;
  const delay=2*hash(instanceId)/4294967295,rate=.96+.08*hash(instanceId+'|rate')/4294967295;let disposed=false,elapsed=0,age=0;
  return{
   update(dt,{visible=true,reducedMotion=false,paused=false}={}){if(disposed)return;check(Number.isFinite(dt)&&dt>=0,'invalid standing host delta');if(!visible||reducedMotion||paused)return;const before=age;age+=dt;const advance=(Math.max(0,age-delay)-Math.max(0,before-delay))*rate;elapsed+=advance;mixer.update(advance);},
   get status(){return{elapsed_s:elapsed,disposed,clip:QUIET_CLIP,source_qualification_mode:QUIET_MODE,derived_sha256:verifiedDerivedSha256,qualification_sha256:qualificationSha256,initial_rest_delay_s:delay,deterministic_playback_rate:rate,clip_duration_s:12,maximum_initial_rest_delay_s:2,minimum_deterministic_playback_rate:.96,required_observation_window_s:requiredObservationSeconds(),mixer_count:disposed?0:1,weight_shift:true,quiet_head_neck:true,tail_gesture:false,independent_ear_motion:false,walk:false,trot:false};},
   dispose(){if(disposed)return;disposed=true;mixer.stopAllAction();mixer.uncacheRoot(root);delete root.userData[OWNER];},
  };
 };
 return Object.freeze({validateHeader,createIdle,qualificationSha256});
}
