// SPDX-License-Identifier: GPL-3.0-or-later
// Real loaded Three/Meshopt hair proof; no renderer or photographic acceptance.
export function inspectHairRuntime(root,{width,height}) {
  const errors=[],meshes=[];
  root.traverse(o=>{if([].concat(o.material||[]).some(m=>m.name==='hair__makehuman_short04'))meshes.push(o);});
  if(!meshes.length)errors.push('no loaded hair mesh');
  const results=[];
  for(const o of meshes){
    const p=o.geometry?.attributes?.position,n=o.geometry?.attributes?.normal,uv=o.geometry?.attributes?.uv,j=o.geometry?.attributes?.skinIndex,w=o.geometry?.attributes?.skinWeight;
    const bones=o.skeleton?.bones||[];
    if(!o.isSkinnedMesh||!bones.length)errors.push(`${o.name}: not an actual loaded SkinnedMesh`);
    if(!p||!n||!uv||!j||!w||![n,uv,j,w].every(a=>a.count===p.count)||p.count<=0){errors.push(`${o.name}: missing/inconsistent decoded attributes`);continue;}
    if(!o.geometry.index||o.geometry.index.count<3||o.geometry.index.count%3)errors.push(`${o.name}: no decoded triangles`);
    const invalidVertexSamples=[];
    let minU=Infinity,maxU=-Infinity,minV=Infinity,maxV=-Infinity,maxWeightError=0,maxNormalError=0;
    for(let i=0;i<p.count;i++){
      const errorsBeforeVertex=errors.length;
      const u=uv.getX(i),v=uv.getY(i),ns=[n.getX(i),n.getY(i),n.getZ(i)];minU=Math.min(minU,u);maxU=Math.max(maxU,u);minV=Math.min(minV,v);maxV=Math.max(maxV,v);
      if(![u,v,...ns,p.getX(i),p.getY(i),p.getZ(i)].every(Number.isFinite))errors.push(`${o.name}: nonfinite decoded vertex ${i}`);
      if(u<-.0001||u>1.0001||v<-.0001||v>1.0001)errors.push(`${o.name}: decoded UV out of bounds at ${i}`);
      const weights=[w.getX(i),w.getY(i),w.getZ(i),w.getW(i)],ids=[j.getX(i),j.getY(i),j.getZ(i),j.getW(i)];const sum=weights.reduce((a,b)=>a+b,0);maxWeightError=Math.max(maxWeightError,Math.abs(sum-1));
      if(weights.some(x=>!Number.isFinite(x)||x<0)||Math.abs(sum-1)>.002||ids.some(x=>!Number.isInteger(x)||x<0||x>=bones.length))errors.push(`${o.name}: invalid decoded skin influence ${i}`);
      const len=Math.hypot(...ns);maxNormalError=Math.max(maxNormalError,Math.abs(len-1));if(!Number.isFinite(len)||Math.abs(len-1)>.005)errors.push(`${o.name}: invalid decoded normal ${i}`);
      if(errors.length>errorsBeforeVertex&&invalidVertexSamples.length<8)invalidVertexSamples.push({index:i,position:[p.getX(i),p.getY(i),p.getZ(i)],uv:[u,v],normal:ns,normal_length:len,joint_indices:ids,weights,weight_sum:sum});
    }
    for(const m of[].concat(o.material)){if(m.name!=='hair__makehuman_short04')continue;
      const image=m.map?.image,actualWidth=image?.width??image?.naturalWidth,actualHeight=image?.height??image?.naturalHeight;
      if(!Number.isFinite(m.alphaTest)||Math.abs(m.alphaTest-.4)>1e-6||m.side!==2)errors.push(`${o.name}: loaded material lost mask/double-sided state`);
      if(!Number.isFinite(m.roughness)||Math.abs(m.roughness-.65)>1e-6||m.metalness!==0)errors.push(`${o.name}: loaded reconstructed roughness/metalness differs`);
      if(actualWidth!==width||actualHeight!==height)errors.push(`${o.name}: loaded texture decode dimensions differ`);
    }
    const attributes=Object.fromEntries(Object.entries({position:p,normal:n,uv,skinIndex:j,skinWeight:w}).map(([name,a])=>[name,{itemSize:a.itemSize,count:a.count,normalized:a.normalized,array_type:a.array?.constructor?.name??a.data?.array?.constructor?.name??null}]));
    const materials=[].concat(o.material).filter(m=>m.name==='hair__makehuman_short04').map(m=>{
      const map=m.map,image=map?.image;
      return{name:m.name,alphaTest:m.alphaTest,side:m.side,roughness:m.roughness,metalness:m.metalness,image:{width:image?.width??image?.naturalWidth??null,height:image?.height??image?.naturalHeight??null,expected_width:width,expected_height:height},map:map?{channel:map.channel,offset:map.offset?.toArray?.()??null,repeat:map.repeat?.toArray?.()??null,rotation:map.rotation,matrixAutoUpdate:map.matrixAutoUpdate,matrix:map.matrix?.toArray?.()??null,flipY:map.flipY}:null};
    });
    results.push({bone_count:bones.length,bone_name_samples:bones.slice(0,64).map(b=>b.name),invalid_vertex_samples:invalidVertexSamples,attributes,materials,name:o.name,vertices:p.count,indices:o.geometry.index?.count,UV_bounds:[minU,maxU,minV,maxV],max_weight_sum_error:maxWeightError,max_normal_length_error:maxNormalError});
  }
  return{passed:errors.length===0,errors,meshes:results,scope:'Actual GLTFLoader decoded SkinnedMesh/UV/weights/normals/image; no photographic or resized-alpha appearance claim'};
}
