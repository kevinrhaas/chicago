// SPDX-License-Identifier: GPL-3.0-or-later
// Loaded Three CPU skin contact measurement; caller supplies a disposable loaded scene.
export function sampleSoleContact(T, gltf, {
  samples=1001, speed_m_s=.6, expected_duration_s=1.2, duty=.62,
  sole_band_m=.0001, ground_y_m=0, forward_world=[0,0,1],
  tolerance_m=.002, provenance=null, raw=true,
}={}) {
  if(!Number.isInteger(samples)||samples<101||samples>10001)throw Error('samples must be 101..10001');
  for(const v of [speed_m_s,expected_duration_s,duty,sole_band_m,ground_y_m,tolerance_m,...forward_world])if(!Number.isFinite(v))throw Error('nonfinite setting');
  if(speed_m_s<=0||expected_duration_s<=0||duty<=.5||duty>=1||sole_band_m<=0||sole_band_m>.001||tolerance_m<=0||tolerance_m>.01||forward_world.length!==3||Math.abs(Math.hypot(...forward_world)-1)>1e-9||Math.abs(forward_world[1])>1e-9)throw Error('invalid bounded contact settings');
  const clips=gltf.animations.filter(c=>c.name==='walk');
  if(clips.length!==1||!Number.isFinite(clips[0].duration)||Math.abs(clips[0].duration-expected_duration_s)>1e-5)throw Error('unique walk clip with expected duration required: '+JSON.stringify({expected_duration_s,tolerance_s:1e-5,walk_count:clips.length,loaded_clips:gltf.animations.map(c=>({name:c.name,duration_s:c.duration,track_time_ranges:c.tracks.map(t=>({name:t.name,samples:t.times.length,first_s:t.times[0]??null,last_s:t.times[t.times.length-1]??null}))}))}));
  const clip=clips[0], declared=clip.userData??{};
  const metadata_comparisons={};
  for(const [key,expected]of [['speed_m_s',speed_m_s],['stance_fraction',duty],['cycle_duration_s',expected_duration_s]]){
    const actual=declared[key], matched=typeof actual==='number'&&Number.isFinite(actual)&&Math.abs(actual-expected)<=1e-6;
    metadata_comparisons[key]={declared:actual??null,expected,tolerance:1e-6,matched};
    if(!matched)throw Error('walk metadata '+key+' must be finite and match expected '+expected);
  }
  metadata_comparisons.loaded_clip_duration_s={declared:clip.duration,expected:expected_duration_s,tolerance:1e-5,matched:true};
  const scene=gltf.scene, bind=[], meshes=[];
  scene.traverse(o=>{bind.push([o,o.position.clone(),o.quaternion.clone(),o.scale.clone(),o.morphTargetInfluences?.slice()]);if(o.isSkinnedMesh)meshes.push(o);});
  if(!meshes.length)throw Error('no loaded skin');
  const mixer=new T.AnimationMixer(scene), v=new T.Vector3();
  function rest(){mixer.stopAllAction();for(const[o,p,q,s,m]of bind){o.position.copy(p);o.quaternion.copy(q);o.scale.copy(s);if(m)o.morphTargetInfluences.splice(0,m.length,...m);}update();}
  function update(){scene.updateMatrixWorld(true);for(const m of meshes)m.skeleton.update();}
  function point(m,i){m.getVertexPosition(i,v).applyMatrix4(m.matrixWorld);const p=v.toArray();if(!p.every(Number.isFinite))throw Error('nonfinite CPU-skinned point');return p;}
  function footwearVertices(m){
    const g=m.geometry, materials=[].concat(m.material), index=g.index;
    const count=index?.count??g.attributes.position.count, ids=new Set();
    const groups=Array.isArray(m.material)&&g.groups.length?g.groups:[{start:0,count,materialIndex:0}];
    for(const group of groups){const material=materials[group.materialIndex];if(!material||!/^footwear(?:__|$)/.test(material.name))continue;
      const lo=Math.max(group.start,g.drawRange.start),hi=Math.min(group.start+group.count,g.drawRange.start+g.drawRange.count,count);
      if(lo%3||Number.isFinite(hi)&&hi%3)throw Error('partial footwear triangle range');
      for(let k=lo;k<hi;k++)ids.add(index?index.getX(k):k);
    }return [...ids];
  }
  let result;
  try {
    rest();const candidates={left:[],right:[]};
    for(let mi=0;mi<meshes.length;mi++){
      const m=meshes[mi], ids=footwearVertices(m);if(!ids.length)continue;
      const si=m.geometry.attributes.skinIndex,sw=m.geometry.attributes.skinWeight;if(!si||!sw||si.itemSize!==4||sw.itemSize!==4)throw Error('footwear requires four-lane loaded skin');
      for(const i of ids){let l=0,r=0,sum=0;for(let lane=0;lane<4;lane++){const w=sw.getComponent(i,lane),bi=si.getComponent(i,lane);if(!Number.isFinite(w)||w<0||!Number.isInteger(bi)||bi<0||bi>=m.skeleton.bones.length)throw Error('invalid footwear skin lane');sum+=w;const name=m.skeleton.bones[bi].name;if(name==='foot_l'||name==='ball_l')l+=w;if(name==='foot_r'||name==='ball_r')r+=w;}
        if(Math.abs(sum-1)>.0001)throw Error('unnormalized footwear skin');
        const side=l>.9&&r<.01?'left':r>.9&&l<.01?'right':null;if(!side)throw Error('ambiguous footwear limb identity');
        candidates[side].push({mesh_index:mi,mesh_name:m.name,vertex_index:i,rest_world:point(m,i)});
      }
    }
    const soles={};for(const side of ['left','right']){const c=candidates[side];if(!c.length)throw Error('missing named '+side+' footwear');const min=Math.min(...c.map(p=>p.rest_world[1]));soles[side]=c.filter(p=>p.rest_world[1]<=min+sole_band_m);if(soles[side].length<3)throw Error('insufficient fixed sole vertices');}
    const action=mixer.clipAction(clip);action.setLoop(T.LoopOnce,1);action.clampWhenFinished=true;
    const rows=[], refs={left:null,right:null};let minY=Infinity,maxStanceHeight=0,maxDrift=0,unsupported=0;
    let firstLocal,lastLocal;
    for(let k=0;k<samples;k++){
      const phase=k/(samples-1),time=phase*clip.duration;
      rest();action.reset();action.play();mixer.setTime(time);update();
      const row={phase,time_s:time,feet:{}};const local=[];let support=0;
      for(const [side,offset]of [['left',0],['right',.5]]){
        const q=(phase+offset)%1,stance=q<duty,points=soles[side].map(p=>point(meshes[p.mesh_index],p.vertex_index));local.push(...points.flat());
        const world=points.map(p=>p.map((value,a)=>value+forward_world[a]*speed_m_s*time));
        const heights=world.map(p=>p[1]-ground_y_m);minY=Math.min(minY,...heights);
        let drift=null;if(stance){support++;if(!refs[side])refs[side]=world;drift=Math.max(...world.map((p,i)=>Math.hypot(p[0]-refs[side][i][0],p[2]-refs[side][i][2])));maxDrift=Math.max(maxDrift,drift);maxStanceHeight=Math.max(maxStanceHeight,...heights.map(Math.abs));}else refs[side]=null;
        row.feet[side]={leg_phase:q,stance,minimum_height_m:Math.min(...heights),maximum_height_m:Math.max(...heights),horizontal_drift_m:drift,...raw?{compensated_world_points_m:world}:{}};
      }
      if(!support)unsupported++;if(k===0)firstLocal=local;if(k===samples-1)lastLocal=local;rows.push(row);
    }
    let loop=0;for(let i=0;i<firstLocal.length;i+=3)loop=Math.max(loop,Math.hypot(...firstLocal.slice(i,i+3).map((x,a)=>x-lastLocal[i+a])));
    result={format:'loaded_human_sole_contact_v1',scope:'Actual loaded CPU morph+skin fixed footwear vertices; discrete samples only. Not source-math, continuous-time, photographic, biological or period acceptance.',provenance,metadata_comparisons,clip:clip.name,duration_s:clip.duration,samples,speed_m_s,duty,ground_y_m,forward_world,sole_band_m,root_motion_compensation:'Adds declared world forward*speed*time; never aligns feet or removes encoded root translation. Input must be disposable and in metric world frame. Encoded root motion therefore contributes to measured drift.',selection:soles,metrics:{minimum_sole_height_m:minY,maximum_stance_absolute_height_m:maxStanceHeight,maximum_stance_horizontal_drift_m:maxDrift,unsupported_samples:unsupported,local_loop_closure_m:loop},tolerance_m,passed:minY>=-tolerance_m&&maxStanceHeight<=tolerance_m&&maxDrift<=tolerance_m&&unsupported===0&&loop<=tolerance_m,raw_samples:rows};
  }finally{rest();mixer.uncacheRoot(scene);}
  return result;
}
