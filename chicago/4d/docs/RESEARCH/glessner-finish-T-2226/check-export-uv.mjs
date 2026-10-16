import fs from 'node:fs';
import path from 'node:path';
const root=process.cwd(),proof='/workspace/t2226-proof';
const {parseGlb,readAccessor}=await import(path.join(root,'tools/k01_contract.mjs'));
const {MeshoptDecoder}=await import(path.join(root,'renderers/web/vendor/three-0.185.1/addons/libs/meshopt_decoder.module.js'));
await MeshoptDecoder.ready;
const expected=JSON.parse(fs.readFileSync(path.join(proof,'expected-gate-uv.json'))),rows=[];
for(const [tier,file] of [['master','assets/gltf/glessner_house__as_built_1887.glb'],['web','assets/web/glessner_house__as_built_1887.glb'],['light','assets/web/glessner_house__as_built_1887.light.glb']]){
 const {json,bin}=parseGlb(fs.readFileSync(file)),ctx={json,bin,views:new Map(),meshopt:MeshoptDecoder},points=[];
 for(const node of json.nodes){
  if(node.mesh===undefined)continue;
  if(node.matrix||node.rotation||node.children)throw Error('Account for additional node transforms');
  const scale=node.scale||[1,1,1],translation=node.translation||[0,0,0];
  for(const prim of json.meshes[node.mesh].primitives){
   const material=json.materials[prim.material];if(material.name!=='oak')continue;
   if(material.pbrMetallicRoughness.baseColorTexture.extensions?.KHR_texture_transform)throw Error('Account for texture transform');
   const pos=readAccessor(ctx,prim.attributes.POSITION),uv=readAccessor(ctx,prim.attributes.TEXCOORD_0);
   for(let i=0;i<pos.length/3;i++)points.push({p:[0,1,2].map(k=>pos[3*i+k]*scale[k]+translation[k]),uv:[uv[2*i],uv[2*i+1]]});
  }
 }
 const positionTolerance=tier==='master'?1e-5:.002,uvTolerance=tier==='master'?1e-5:.002;
 let maxPositionError=0,maxUvError=0;
 for(const e of expected){
  const candidates=points.map(q=>({...q,pe:Math.hypot(...q.p.map((v,k)=>v-e.position[k])),ue:Math.hypot(...q.uv.map((v,k)=>v-e.uv[k]))})).filter(q=>q.pe<=positionTolerance).sort((a,b)=>a.ue-b.ue);
  if(!candidates.length||candidates[0].ue>uvTolerance)throw Error(JSON.stringify({tier,expected:e,best:candidates[0],positionTolerance,uvTolerance}));
  maxPositionError=Math.max(maxPositionError,candidates[0].pe);maxUvError=Math.max(maxUvError,candidates[0].ue);
 }
 rows.push({tier,checkedCorners:expected.length,maxPositionError,maxUvError,positionTolerance,uvTolerance});
}
fs.writeFileSync(path.join(proof,'export-uv-validation.json'),JSON.stringify({method:'Decode actual master, meshopt Full and meshopt Light; apply node scale/translation; compare each expected gate member corner and metric UV through glTF V flip. Web tolerances 2 mm position and 0.002 UV cycles; master 0.01 mm and 0.00001 cycles.',rows},null,2)+'\n');console.log(JSON.stringify(rows,null,2));
