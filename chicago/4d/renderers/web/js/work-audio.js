// SPDX-License-Identifier: GPL-3.0-or-later
// Recorded sparse impacts, only from the visible generated tool's actual contact serial.
export const WORK_RECORDING = Object.freeze({id:'hammer-nail',encodedBytes:384812,
  sha256:'ef84f820c11c538ca8276e0303c89de16de02de30a643fe183e29ed39b34526c',
  offset:21.526,duration:.36,sampleRate:48000,sourceSeconds:24});
export const WORK_AUDIO_LIMITS=Object.freeze({voices:1,retainedBytes:128*1024,peakDecodeBytes:5*1024*1024,
  contactAgeMs:120,sourceAgeMs:250,maxRadius:24,minImpactGapMs:500});
const finite=Number.isFinite;
const point=p=>p&&[p.x,p.y,p.z].every(finite);
const actorId='hi_town_chicago_militia_unnamed_4_1812';
const tasks=new Set(['militia-piazza-repair','militia-packing-chest']);
const validDate=s=>/^1812-\d{2}-\d{2}$/.test(s??'');
const hashBytes=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');

/** The catalog binds exact dates/hours as well as scene, actor and action. */
export function workPolicy(catalog,{scene,date,hour}={}) {
  if(scene!=='1812'||!validDate(date)||!finite(hour))return null;
  const a=Array.isArray(catalog?.assets)?catalog.assets.find(a=>a.id===WORK_RECORDING.id):null,p=a?.scene_placement;
  if(a?.runtime_enabled!==true||!Array.isArray(a.approved_eras)||!a.approved_eras.includes(scene)
    ||a.delivery?.sha256!==WORK_RECORDING.sha256||a.delivery?.bytes!==WORK_RECORDING.encodedBytes||typeof a.url!=='string'
    ||p?.mode!=='visible-work'||!finite(p.gain)||p.gain<=0||p.gain>.25
    ||!finite(p.max_distance_m)||p.max_distance_m<=0||p.max_distance_m>WORK_AUDIO_LIMITS.maxRadius
    ||p.cue?.offset_s!==WORK_RECORDING.offset||p.cue?.duration_s!==WORK_RECORDING.duration||!Array.isArray(p.bindings))return null;
  const bindings=p.bindings.filter(b=>b?.scene===scene&&validDate(b.dates?.from)&&validDate(b.dates?.to)
    &&date>=b.dates.from&&date<=b.dates.to&&Array.isArray(b.hours)&&b.hours.some(h=>Array.isArray(h)&&h.length===2&&h.every(finite)&&hour>=h[0]&&hour<h[1])
    &&Array.isArray(b.actor_ids)&&b.actor_ids.includes(actorId)&&Array.isArray(b.action_ids)&&b.action_ids.includes('nail-wood')
    &&Array.isArray(b.task_ids)&&b.task_ids.some(id=>tasks.has(id)));
  if(!bindings.length)return null;
  return{asset:a,bindings,gain:p.gain,radius:p.max_distance_m,key:JSON.stringify([scene,date,a.url,p])};
}
export function workCandidate(policy,sources,{scene,date,hour,eye,now}={}) {
  if(!policy||!point(eye)||!finite(now))return null;
  const candidates=[];
  for(const s of (Array.isArray(sources)?sources:[]).slice(0,8)){
    if(!s||s.actorId!==actorId||!tasks.has(s.id)||s.actionId!=='nail-wood'||s.scene!==scene||s.date!==date||s.hour!==hour
      ||s.visible!==true||s.working!==true||!Number.isSafeInteger(s.session)||s.session<0
      ||!Number.isSafeInteger(s.contactSerial)||s.contactSerial<0||!point(s.anchor)
      ||!finite(s.updatedAt)||now-s.updatedAt<0||now-s.updatedAt>WORK_AUDIO_LIMITS.sourceAgeMs
      ||!policy.bindings.some(b=>b.actor_ids.includes(s.actorId)&&b.action_ids.includes(s.actionId)&&b.task_ids.includes(s.id)))continue;
    const distance=Math.hypot(s.anchor.x-eye.x,s.anchor.y-eye.y,s.anchor.z-eye.z);
    if(distance>=policy.radius)continue;
    candidates.push({source:s,distance,gain:policy.gain*(1-distance/policy.radius)**2,key:`${s.id}:${s.session}`});
  }
  // A duplicate source identity is ambiguous, not a reason to layer two sounds.
  if(candidates.length!==1)return null;
  return candidates[0];
}
export function createWorkAudio({ctx,output,catalog,decodeAudio,fetcher=globalThis.fetch?.bind(globalThis),base,
  now=()=>performance.now(),hashAudio=hashBytes,onError=()=>{}}={}) {
  let disposed=false,generation=0,scope='',buffer=null,loading=null,controller=null,voice=null,failed=false,duck=1;
  let observed=null,lastStartedAt=-Infinity,started=0,lastContact=null;
  const errors=new Set();
  const report=message=>{errors.add(message);onError(message);};
  const retained=()=>buffer?buffer.length*buffer.numberOfChannels*4:0;
  function release(v){v.source.onended=null;for(const n of [v.source,v.envelope,v.gain,v.pan])n.disconnect();if(voice===v)voice=null;}
  function stop(immediate=false){const v=voice;if(!v)return;
    if(immediate){try{v.source.stop();}catch{}release(v);}
    else if(!v.stopping){v.stopping=true;v.gain.gain.cancelScheduledValues(ctx.currentTime);
      v.gain.gain.setValueAtTime(v.gain.gain.value,ctx.currentTime);v.gain.gain.linearRampToValueAtTime(0,ctx.currentTime+.015);
      v.source.stop(ctx.currentTime+.015);}
  }
  function reset(){generation++;scope='';observed=null;buffer=null;failed=false;stop(true);controller?.abort();controller=null;
    // Hold the decoder reservation until a non-cancellable decode finishes.
  }
  async function load(policy){
    if(disposed||loading||buffer||failed)return;
    const own=generation,token={},abort=new AbortController();loading=token;controller=abort;
    try{
      const response=await fetcher(new URL(policy.asset.url,base),{signal:abort.signal});
      if(!response.ok)throw Error(`HTTP ${response.status}`);
      const bytes=await response.arrayBuffer();if(disposed||own!==generation)return;
      if(bytes.byteLength!==WORK_RECORDING.encodedBytes)throw Error('work recording delivery size mismatch');
      if(await hashAudio(bytes)!==WORK_RECORDING.sha256)throw Error('work recording differs from measured source window');
      if(disposed||own!==generation)return;
      const whole=await decodeAudio(bytes);if(disposed||own!==generation)return;
      const count=Math.round(WORK_RECORDING.duration*whole.sampleRate),offset=Math.round(WORK_RECORDING.offset*whole.sampleRate);
      const peak=(whole.length+count)*4;
      if(whole.numberOfChannels!==1||whole.sampleRate!==WORK_RECORDING.sampleRate||!Number.isSafeInteger(whole.length)
        ||whole.length<=0||!finite(whole.duration)||whole.duration>WORK_RECORDING.sourceSeconds+.001
        ||offset+count>whole.length||peak>WORK_AUDIO_LIMITS.peakDecodeBytes||count*4>WORK_AUDIO_LIMITS.retainedBytes)
        throw Error('work recording exceeds mono 48kHz / 5MiB peak or pulse bounds');
      const pulse=ctx.createBuffer(1,count,whole.sampleRate);
      pulse.getChannelData(0).set(whole.getChannelData(0).subarray(offset,offset+count));
      buffer=pulse; // Retain only 0.36s / 69,120B; no source scheduling from async completion.
    }catch(e){if(own===generation&&!disposed&&e.name!=='AbortError'){failed=true;report(`hammer-nail: ${e.message}`);}}
    finally{if(loading===token)loading=null;if(controller===abort)controller=null;}
  }
  function start(candidate){
    if(voice||!buffer||disposed)return;
    const source=ctx.createBufferSource(),envelope=ctx.createGain(),gain=ctx.createGain(),pan=ctx.createPanner();
    source.buffer=buffer;source.loop=false;source.playbackRate.value=1;gain.gain.value=candidate.gain*duck;
    pan.panningModel='HRTF';pan.rolloffFactor=0;
    for(const axis of ['x','y','z'])pan[`position${axis.toUpperCase()}`].value=candidate.source.anchor[axis];
    source.connect(envelope);envelope.connect(gain);gain.connect(pan);pan.connect(output);
    const t=ctx.currentTime,duration=buffer.duration;
    envelope.gain.setValueAtTime(0,t);envelope.gain.linearRampToValueAtTime(1,t+.001);
    envelope.gain.setValueAtTime(1,t+duration-.035);envelope.gain.linearRampToValueAtTime(0,t+duration);
    const v={source,envelope,gain,pan,key:candidate.key,level:candidate.gain,stopping:false};voice=v;
    source.onended=()=>release(v);
    try{source.start(t);lastStartedAt=now();started++;lastContact={taskId:candidate.source.id,session:candidate.source.session,
      serial:candidate.source.contactSerial,at:candidate.source.contactAt,anchor:{...candidate.source.anchor}};}
    catch(e){release(v);failed=true;report(`hammer-nail: ${e.message}`);}
  }
  return{
    frame({enabled,scene,date,hour,eye,sources}={}){
      if(disposed)return;
      if(!enabled||!output||!point(eye)){if(scope||voice||buffer||loading)reset();return;}
      const policy=workPolicy(catalog(),{scene,date,hour});
      if(!policy){if(scope||voice||buffer||loading)reset();return;}
      if(scope!==policy.key){reset();scope=policy.key;}
      const time=now(),candidate=workCandidate(policy,typeof sources==='function'?sources():sources,{scene,date,hour,eye,now:time});
      if(!candidate){reset();return;}
      const s=candidate.source;
      if(!observed||observed.key!==candidate.key||s.contactSerial<observed.serial){stop(true);observed={key:candidate.key,serial:s.contactSerial};}
      else if(s.contactSerial!==observed.serial){
        const next=s.contactSerial===observed.serial+1;observed.serial=s.contactSerial; // consume even if late/unready
        const fresh=finite(s.contactAt)&&time-s.contactAt>=0&&time-s.contactAt<=WORK_AUDIO_LIMITS.contactAgeMs;
        if(next&&fresh&&buffer&&!voice&&time-lastStartedAt>=WORK_AUDIO_LIMITS.minImpactGapMs)start(candidate);
      }
      if(voice&&!voice.stopping){voice.level=candidate.gain;voice.gain.gain.setTargetAtTime(candidate.gain*duck,ctx.currentTime,.02);}
      if(!buffer&&!failed)void load(policy);
    },
    reset,
    setDuck(value){duck=finite(value)?Math.max(0,Math.min(1,value)):0;if(voice&&!voice.stopping)voice.gain.gain.setTargetAtTime(voice.level*duck,ctx.currentTime,.02);},
    get state(){return{voices:voice?[voice.key]:[],decodedBytes:retained(),loading:loading?1:0,failed,started,lastContact,errors:[...errors]};},
    dispose(){if(disposed)return;reset();disposed=true;},
  };
}
