// SPDX-License-Identifier: GPL-3.0-or-later
// Finite settler observation helpers. No decoder, adoption, pose or photo certificate.
// Passed directly to Playwright so this same tested guard executes in the page.
// Legacy readiness is unchanged; opt-in cannot race the asynchronous helper import.
export function inspectorReady({seatMode,api=globalThis.teamsterInspection}){
  return !!api?.ready&&(!seatMode||['prepareSeatReview','measureSeatReview','seatView']
    .every(key=>typeof api[key]==='function'));
}
export const ASSET = 'settler_1812';
export const LINEN_PATCH = '494362d1bee5cd0088be4239d3e2bac0d0f95b1686a9dd1d0f45f244ce0ecaa2';
export const LIMITS = Object.freeze({scanTriangles:100000, proxyTriangles:4096, matrices:256,
  matrixMagnitude:1e6, rays:63, rayTrianglePairs:258048, nearHitRecords:8,
  bytesPerLod:8*1024*1024, picturesPerLod:26,webBytes:16*1024*1024});
export const POSES = Object.freeze([{clip:'idle',phase:0},
  ...Array.from({length:8},(_,i)=>({clip:'walk',phase:i/8}))]);
export const OBSERVER_FILES=Object.freeze(['tools/human_teamster.mjs','tools/human_teamster.html',
  'tools/human_settler_seat_review.mjs','tools/human_frame_compare.js','tools/human_sole_contact.mjs',
  'tools/human_hair_runtime.mjs','data/humans/contract.json']);
const need=(ok,message)=>{if(!ok)throw Error('settler seat observation: '+message);};
const sha=/^[a-f0-9]{64}$/,commit=/^[a-f0-9]{40}$/;
export function validatePose(pose){
  need(POSES.some(p=>p.clip===pose?.clip&&p.phase===pose?.phase),'finite actual idle/walk schedule only');return pose;
}
export function captureViews(pose){
  validatePose(pose);const views=[{angle:'rear',close:true}];
  if(pose.clip==='idle')views.push({angle:'rear',close:false});
  if(pose.clip==='idle'||pose.phase===.25||pose.phase===.75)views.push({angle:'rearquarter',close:true});
  return views;
}
export const parentFiles=()=>['assets/humans/','assets/humans/web/'].flatMap(prefix=>
  [0,1,2,3].map(lod=>prefix+ASSET+'.lod'+lod+'.glb'));

export function validateRequest(request,receipt){
  need(request?.schema==='t1789_settler_seat_observer_request_v1'
    &&request.status==='BOUND_FOR_NATIVE_OBSERVATION','reviewed bound request required');
  need(request.asset_id===ASSET&&request.release===false&&request.native_fit_accepted===false,
    'one settler only; no release or fit promotion');
  need(['before','after'].includes(request.role)&&commit.test(request.source_commit??'')
    &&sha.test(request.receipt_sha256??''),'typed immutable source and receipt bindings');
  need(commit.test(request.observer_base_commit??'')&&commit.test(request.runtime_base_commit??'')
    &&sha.test(request.runtime_inventory_sha256??''),'separate observer/runtime source and inventory lineage');
  need(Array.isArray(request.observer_files)&&request.observer_files.length===OBSERVER_FILES.length
    &&new Set(request.observer_files.map(r=>r.file)).size===OBSERVER_FILES.length,'closed observer code/resource bindings');
  for(const row of request.observer_files)need(OBSERVER_FILES.includes(row.file)&&sha.test(row.sha256??''),'bound actual observer resources');
  need(request.role!=='after'||request.source_patch_sha256===LINEN_PATCH,'exact linen source candidate');
  const expected=new Set(parentFiles()),rows=request.parents;
  need(Array.isArray(rows)&&rows.length===8&&new Set(rows.map(r=>r.file)).size===8,
    'exact eight MASTER/WEB parent bindings');
  for(const row of rows)need(expected.has(row.file)&&sha.test(row.sha256??'')
    &&Number.isSafeInteger(row.bytes)&&row.bytes>=20&&(!row.file.includes('/web/')||row.bytes<=LIMITS.webBytes),
    'complete bounded actual parent facts; unknowns cannot run');
  const source=new Map();
  if(request.role==='before'){
    need(request.receipt_kind==='fixture_baseline'&&Array.isArray(receipt?.files),'existing fixture baseline receipt');
    for(const row of receipt.files){
      need(!source.has(row.file),'duplicate baseline binding');source.set(row.file,row);
    }
    for(const row of rows){const prior=source.get(row.file);need(prior?.verdicts?.length
      &&prior.verdicts.every(v=>v.ok===true),'selected pre-existing baseline must pass');}
  }else{
    need(request.receipt_kind==='canonical_capture'&&commit.test(request.definition_commit??'')
      &&receipt?.schema==='t1789_canonical_parent_capture_v2'
      &&receipt.status==='CANONICAL_PARENT_CAPTURE_ONLY'&&receipt.phase==='CLOSED'
      &&receipt.source_sha===request.source_commit&&receipt.definition_sha===request.definition_commit,
      'closed actual canonical capture lineage');
    need(receipt.release===false&&receipt.install===false&&receipt.material_applied===false
      &&receipt.native_fit_accepted===false,'capture-only parents, no adoption');
    need(Array.isArray(receipt.parent_hashes)&&receipt.parent_hashes.length===8,'closed captured eight');
    for(const row of receipt.parent_hashes){
      const prefix=ASSET+'/parents/';need(row.file.startsWith(prefix),'captured family prefix');
      const file=row.file.slice(prefix.length);need(expected.has(file)&&!source.has(file),'captured membership');
      source.set(file,row);
    }
  }
  for(const row of rows){const prior=source.get(row.file);need(prior&&prior.sha256===row.sha256
    &&prior.bytes===row.bytes,'parent differs from actual receipt: '+row.file);}
  return new Map(rows.map(r=>[r.file,r]));
}

export function validateRuntimeInventory(request,inventory){
  need(inventory?.schema==='t1789_native_runtime_inventory_v1'
    &&inventory.runtime_base_commit===request.runtime_base_commit,'actual published projection lineage');
  need(Array.isArray(inventory.files)&&inventory.files.length>0&&inventory.files.length<=20000,'bounded published resource inventory');
  const result=new Map();
  for(const row of inventory.files){
    need(typeof row.file==='string'&&!row.file.startsWith('/')&&!row.file.includes('\\')
      &&row.file.split('/').every(p=>p&&p!=='.'&&p!=='..')&&!result.has(row.file)
      &&sha.test(row.sha256??'')&&Number.isSafeInteger(row.bytes)&&row.bytes>=0,'unique safe published resource facts');
    result.set(row.file,row);
  }
  for(const parent of request.parents.filter(r=>r.file.includes('/web/'))){
    const file=parent.file.replace(/^assets\/humans\//,'data/humans/'),row=result.get(file);
    need(row&&row.sha256===parent.sha256&&row.bytes===parent.bytes,'runtime WEB differs from bound parent');
  }
  return result;
}

export function validateBeforeObservation(request,before,lods){
  need(request.role==='after'&&before?.schema==='t1789_settler_native_seat_observation_v1'
    &&['NATIVE_SAMPLED_OBSERVATION_COMPLETE','NATIVE_OBSERVATION_NONPASS'].includes(before.status)
    &&before.request?.role==='before'&&before.request.asset_id===ASSET&&before.native_fit_accepted===false,
    'complete actual before observer; no fit promotion');
  need(request.observer_files.every(row=>before.request.observer_files?.some(b=>b.file===row.file&&b.sha256===row.sha256)),
    'same actual observer code/resources before and after');
  need(Array.isArray(before.runs)&&new Set(before.runs.map(r=>r.file+'|'+r.viewport_name)).size===before.runs.length,
    'unique before observation runs');
  for(const lod of lods)for(const [label,width,height]of [['desktop',1280,800],['mobile',390,780]]){
    const run=before.runs.find(r=>r.file===`assets/humans/web/${ASSET}.lod${lod}.glb`&&r.viewport_name===label);
    need(run?.complete&&run.viewport?.width===width&&run.viewport.height===height
      &&run.poses?.length===POSES.length&&run.screenshots?.length===13,'matching complete before viewport/pose/image matrix');
    need(POSES.every(p=>run.poses.filter(r=>r.pose?.clip===p.clip&&r.pose?.phase===p.phase).length===1),'one before measurement per real pose');
    for(const pose of POSES)for(const camera of captureViews(pose)){
      const images=run.screenshots.filter(r=>r.actual_pose?.clip===pose.clip&&r.actual_pose?.phase===pose.phase
        &&r.angle===camera.angle&&r.close===camera.close);
      need(images.length===1,'exact before pose/camera correspondence');
      for(const key of ['camera_world','camera_projection'])need(Array.isArray(images[0][key])
        &&images[0][key].length===16&&images[0][key].every(Number.isFinite),'finite actual before camera matrices');
    }
  }
  return before;
}

export function checkBudget({triangles,rays=LIMITS.rays,matrices=0}){
  need(Number.isInteger(triangles)&&triangles>0&&triangles<=LIMITS.proxyTriangles,'proxy triangle cap');
  need(Number.isInteger(rays)&&rays>0&&rays<=LIMITS.rays,'ray cap');
  need(triangles*rays<=LIMITS.rayTrianglePairs,'ray/triangle pair cap');
  need(Number.isInteger(matrices)&&matrices>=0&&matrices<=LIMITS.matrices,'matrix cap');
  return {triangles,rays,maximum_triangle_tests:triangles*rays,matrices};
}

export function signedRearGap(bodyHits,garmentHits){
  for(const hits of [bodyHits,garmentHits])need(hits.every(h=>Number.isFinite(h.distance)&&h.distance>=0),'finite ray distances');
  const body=bodyHits.length?Math.min(...bodyHits.map(h=>h.distance)):null;
  const garment=garmentHits.length?Math.min(...garmentHits.map(h=>h.distance)):null;
  return {body_hit:body!==null,garment_hit:garment!==null,
    posterior_ray_gap_m:body!==null&&garment!==null?body-garment:null,
    body_without_garment:body!==null&&garment===null,
    sampled_breakthrough:body!==null&&garment!==null&&body-garment<0};
}

// The native inspector supplies its existing THREE instance and loaded scene.
export function nativeSeatObserver(T,state){
  let selection=null;
  const world=(mesh,index)=>mesh.getVertexPosition(index,new T.Vector3()).applyMatrix4(mesh.matrixWorld);
  const materialNames=mesh=>[].concat(mesh.material).map(m=>m.name);
  function sourceTriangles(predicate){
    const rows=[];let scanned=0;
    for(const mesh of state().skin){
      const geometry=mesh.geometry,count=geometry.index?.count??geometry.attributes.position.count;
      const groups=geometry.groups.length?geometry.groups:[{start:0,count,materialIndex:0}],seen=new Set();
      for(const group of groups){
        if(!predicate(materialNames(mesh)[group.materialIndex??0]??''))continue;
        const start=Math.max(group.start,geometry.drawRange.start),end=Math.min(group.start+group.count,count,geometry.drawRange.start+geometry.drawRange.count);
        need(start%3===0&&Number.isFinite(end)&&end%3===0,'complete drawn triangle ranges');
        for(let offset=start;offset<end;offset+=3){
          need(++scanned<=LIMITS.scanTriangles,'source scan cap');if(seen.has(offset))continue;seen.add(offset);
          const ids=[0,1,2].map(k=>geometry.index?geometry.index.getX(offset+k):offset+k);
          rows.push({mesh,offset,ids,bind:ids.map(i=>world(mesh,i))});
        }
      }
    }
    need(rows.length>0,'required native material role absent');return rows;
  }
  function matrixFacts(){
    const s=state(),matrices=[],skeletons=new Set(s.skin.map(m=>m.skeleton));
    for(const mesh of s.skin)for(const matrix of [mesh.matrixWorld,mesh.bindMatrix,mesh.bindMatrixInverse])matrices.push(matrix);
    for(const skeleton of skeletons)for(let i=0;i<skeleton.bones.length;i++){
      matrices.push(skeleton.bones[i].matrixWorld);
      matrices.push(new T.Matrix4().fromArray(skeleton.boneMatrices,i*16));
    }
    need(matrices.length<=LIMITS.matrices,'matrix cap');let maximum=0,minimumDeterminant=Infinity;
    const values=[];
    for(const matrix of matrices){
      need(matrix.elements.every(Number.isFinite),'nonfinite native matrix');
      const determinant=Math.abs(matrix.determinant());need(determinant>1e-12,'singular native matrix');
      minimumDeterminant=Math.min(minimumDeterminant,determinant);
      for(const value of matrix.elements){maximum=Math.max(maximum,Math.abs(value));values.push(value);}
    }
    need(maximum<=LIMITS.matrixMagnitude,'matrix magnitude cap');
    return {count:matrices.length,maximum_absolute_element:maximum,minimum_absolute_determinant:minimumDeterminant,
      finite_and_nonsingular:true,scope:'numeric validity only; not rigid-frame, normals, shading or all-pose proof',values};
  }
  async function prepare(){
    const s=state();need(s.header?.scenes?.[0]?.extras?.chicago4d_human?.asset_id===ASSET,'actual native asset identity');
    s.rest();s.update();const body=sourceTriangles(name=>name==='skin'||name.startsWith('skin__'));
    const garment=sourceTriangles(name=>name==='garment_lower__trousers_linen_1810');
    const pelvis=s.skin[0].skeleton.bones.find(b=>b.name==='pelvis');need(pelvis,'native pelvis bone');
    // Existing inspector rest frame is measured from all actual visible mesh vertices.
    // Skin under trousers may be deliberately absent; never fabricate it for this diagnostic.
    need(s.frame?.min?.length===3&&s.frame?.max?.length===3&&[...s.frame.min,...s.frame.max].every(Number.isFinite),'actual whole-mesh rest frame required');
    const frame=new T.Box3(new T.Vector3().fromArray(s.frame.min),new T.Vector3().fromArray(s.frame.max));
    const h=frame.max.y-frame.min.y,scale=h/1.75,pelvisPosition=pelvis.getWorldPosition(new T.Vector3());
    need(h>.9&&h<2.3,'canonical body metric frame');
    const region={lo:pelvisPosition.y-.16*scale,hi:frame.min.y+h*.585-.008*scale,
      x:pelvisPosition.x,z:pelvisPosition.z,half:.14*scale,scale};
    need(region.hi>region.lo,'positive declared seat interval');
    const selected=rows=>rows.filter(row=>{
      const xs=row.bind.map(p=>p.x),ys=row.bind.map(p=>p.y),zs=row.bind.map(p=>p.z),margin=.025*scale;
      return Math.min(...xs)<=region.x+region.half+margin&&Math.max(...xs)>=region.x-region.half-margin
        &&Math.min(...ys)<=region.hi+margin&&Math.max(...ys)>=region.lo-margin&&Math.min(...zs)<=region.z+.035*scale;
    });
    selection={body:selected(body),garment:selected(garment),pelvis,bindPelvisInverse:pelvis.matrixWorld.clone().invert(),region};
    // Camera bounds use clipped barycentrics of the actual source triangles. At a
    // pose these interpolate already-skinned positions, never position/weight pairs.
    const margin=.025*scale;
    for(const row of selection.garment){
      let polygon=row.bind.map((p,i)=>({p,w:[0,1,2].map(j=>i===j?1:0)}));
      for(const field of [p=>p.x-region.x+region.half+margin,p=>region.x+region.half+margin-p.x,
        p=>p.y-region.lo+margin,p=>region.hi+margin-p.y,p=>region.z+.035*scale-p.z]){
        const next=[];
        for(let i=0;i<polygon.length;i++){
          const a=polygon[i],b=polygon[(i+1)%polygon.length],da=field(a.p),db=field(b.p);
          if(da>=0)next.push(a);
          if(da*db<0){const t=da/(da-db);next.push({p:a.p.clone().lerp(b.p,t),w:a.w.map((w,j)=>w*(1-t)+b.w[j]*t)});}
        }
        polygon=next;
      }
      row.cameraBarycentrics=polygon.map(p=>p.w);
    }
    const matrices=matrixFacts();checkBudget({triangles:selection.body.length+selection.garment.length,matrices:matrices.count});
    need(selection.garment.length,'nonempty selected native trouser role');
    return {asset:ASSET,region,selected_triangles:{body:selection.body.length,garment:selection.garment.length},
      bind_selection:'frozen posterior material-role triangles; current pose never changes membership',native_fit_accepted:false};
  }
  function proxy(rows){
    const values=[];for(const row of rows)for(const i of row.ids){const p=world(row.mesh,i);values.push(p.x,p.y,p.z);}
    need(values.every(Number.isFinite),'nonfinite posed native vertex');
    const geometry=new T.BufferGeometry();geometry.setAttribute('position',new T.BufferAttribute(new Float64Array(values),3));
    geometry.computeBoundingBox();geometry.computeBoundingSphere();
    const material=new T.MeshBasicMaterial({side:T.DoubleSide}),mesh=new T.Mesh(geometry,material);mesh.updateMatrixWorld(true);
    return {mesh,values,dispose(){geometry.dispose();material.dispose();}};
  }
  async function measure(pose){
    need(selection,'prepare native seat selection first');
    validatePose(pose);
    const s=state();s.setClip(pose.clip,pose.phase);s.update();const facts=matrixFacts(),{values,...matrix}=facts;
    const raw=new ArrayBuffer(values.length*8),view=new DataView(raw);values.forEach((v,i)=>view.setFloat64(i*8,v,true));
    matrix.float64_le_sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)),v=>v.toString(16).padStart(2,'0')).join('');
    const body=proxy(selection.body),garment=proxy(selection.garment),rays=[];
    try{
      const delta=selection.pelvis.matrixWorld.clone().multiply(selection.bindPelvisInverse);
      const outward=new T.Vector3(0,0,-1).applyNormalMatrix(new T.Matrix3().getNormalMatrix(delta)),all=[...body.values,...garment.values];
      let maximum=-Infinity,minimum=Infinity;
      for(let i=0;i<all.length;i+=3){const d=new T.Vector3(all[i],all[i+1],all[i+2]).dot(outward);maximum=Math.max(maximum,d);minimum=Math.min(minimum,d);}
      const caster=new T.Raycaster(),far=maximum-minimum+.2*selection.region.scale;
      function nearest(hits,role){
        const first=hits[0]?.distance,candidates=first===undefined?[]:hits.filter(h=>Math.abs(h.distance-first)<=1e-7);
        need(candidates.length<=LIMITS.nearHitRecords,'nearest-hit record cap');
        return {distance:first??null,near_candidates:candidates.map(h=>({distance:h.distance,point:h.point.toArray(),
          source_mesh:selection[role][h.faceIndex].mesh.name,source_triangle_offset:selection[role][h.faceIndex].offset})),
          coincidence_scope:'all native nearest ties retained within 0.1 micrometre; minimum raw distance used, never a clearance allowance'};
      }
      for(let row=0;row<7;row++)for(let col=0;col<9;col++){
        const r=selection.region,p=new T.Vector3(r.x+r.half*(2*col/8-1),r.lo+(r.hi-r.lo)*row/6,r.z).applyMatrix4(delta);
        const origin=p.clone().addScaledVector(outward,maximum-p.dot(outward)+.1*r.scale);
        caster.set(origin,outward.clone().negate());caster.near=0;caster.far=far;
        const bh=selection.body.length?caster.intersectObject(body.mesh,false):[],gh=caster.intersectObject(garment.mesh,false);
        rays.push({row,col,origin:origin.toArray(),direction:caster.ray.direction.toArray(),
          ...signedRearGap(bh,gh),body_nearest:nearest(bh,'body'),garment_nearest:nearest(gh,'garment')});
      }
      const covered=rays.filter(r=>r.body_hit&&r.garment_hit),bodyCount=rays.filter(r=>r.body_hit).length;
      return {pose,matrix,budget:checkBudget({triangles:selection.body.length+selection.garment.length,matrices:matrix.count}),
        rays,body_hit_count:bodyCount,paired_hit_count:covered.length,
        minimum_sampled_posterior_ray_gap_m:covered.length?Math.min(...covered.map(r=>r.posterior_ray_gap_m)):null,
        sampled_negative_gap_count:rays.filter(r=>r.sampled_breakthrough).length,
        body_without_garment_count:rays.filter(r=>r.body_without_garment).length,
        diagnostic_execution_complete:true,paired_body_surface_available:covered.length>0,
        diagnostic_status:bodyCount===0?'UNAVAILABLE_NO_POSTERIOR_BODY_HITS':covered.length===0?'UNAVAILABLE_NO_PAIRED_HITS':'SAMPLED_WITNESSES_AVAILABLE',native_fit_accepted:false,
        scope:'63 posterior rays through actual retained skin and trousers; hidden body polygons are not reconstructed, DoubleSide, nearest actual posed triangles. Not Euclidean clearance, SAT separation, MTD, all-triangle contact, self-intersection, opacity/shading or town/runtime fit.'};
    }finally{body.dispose();garment.dispose();}
  }
  function points(){
    need(selection,'prepare first');const result=[];
    for(const row of selection.garment){const vertices=row.ids.map(i=>world(row.mesh,i));
      for(const weights of row.cameraBarycentrics){const p=new T.Vector3();weights.forEach((w,i)=>p.addScaledVector(vertices[i],w));result.push(p.x,p.y,p.z);}
    }
    need(result.length>0,'no actual seat triangle support for camera');return result;
  }
  return {prepare,measure,points};
}
