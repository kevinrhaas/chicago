// Original finite CPU geometry/Mixer check. No WebGL, image decode or world proof.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
const here = new URL('../', import.meta.url);
const app = here;
const vendor = new URL('renderers/web/vendor/three-0.185.1/', app);
const three = new URL('three.core.js', vendor).href;
const THREE = await import(three);
const data = text => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const utils = {};
for (const name of ['BufferGeometryUtils', 'SkeletonUtils']) {
  utils[name] = data((await fs.readFile(new URL(`addons/utils/${name}.js`, vendor), 'utf8')).replace("from 'three'", `from '${three}'`));
}
const gltfURL = new URL('addons/loaders/GLTFLoader.js', vendor);
const source = (await fs.readFile(gltfURL, 'utf8')).replace(/from '([^']+)'/g, (_, spec) => {
  const name = Object.keys(utils).find(k => spec.endsWith(`/${k}.js`));
  return `from '${spec === 'three' ? three : name ? utils[name] : new URL(spec, gltfURL).href}'`;
});
const { GLTFLoader } = await import(data(source));
const { MeshoptDecoder } = await import(new URL('addons/libs/meshopt_decoder.module.js', vendor));
await MeshoptDecoder.ready;
globalThis.self ??= globalThis;
function geometryOnly(bytes) {
  const n = bytes.readUInt32LE(12), doc = JSON.parse(bytes.subarray(20, 20+n));
  // Geometry streams, skin, nodes and animation are untouched. Texture decode is
  // deliberately outside this CPU test and stays a real-browser requirement.
  for (const m of doc.materials ?? []) {
    delete m.normalTexture; delete m.occlusionTexture; delete m.emissiveTexture;
    if (m.pbrMetallicRoughness) { delete m.pbrMetallicRoughness.baseColorTexture; delete m.pbrMetallicRoughness.metallicRoughnessTexture; }
  }
  const json0=Buffer.from(JSON.stringify(doc)), json=Buffer.concat([json0,Buffer.alloc(-json0.length&3,32)]);
  const bin=bytes.subarray(28+n), out=Buffer.alloc(28+json.length+bin.length);
  out.writeUInt32LE(0x46546c67,0);out.writeUInt32LE(2,4);out.writeUInt32LE(out.length,8);
  out.writeUInt32LE(json.length,12);out.writeUInt32LE(0x4e4f534a,16);json.copy(out,20);
  out.writeUInt32LE(bin.length,20+json.length);out.writeUInt32LE(0x004e4942,24+json.length);bin.copy(out,28+json.length);
  return out.buffer.slice(out.byteOffset,out.byteOffset+out.byteLength);
}
const vehicleURL=new URL('renderers/web/transport/parked-brougham/brougham-near.glb',app);
const vehicleBytes=await fs.readFile(vehicleURL);
const vehicleSHA=crypto.createHash('sha256').update(vehicleBytes).digest('hex');
const vehicleMetadata=JSON.parse(await fs.readFile(new URL('renderers/web/transport/parked-brougham/brougham.json',app),'utf8'));
assert.equal(vehicleSHA,vehicleMetadata.lods.find(l=>l.detail==='near').indexed_sha256);
const vehicle=await new GLTFLoader().parseAsync(geometryOnly(vehicleBytes),'');
vehicle.scene.updateMatrixWorld(true);
const footTriangles=[];
vehicle.scene.traverse(o=>{
  if(!o.isMesh)return;
  const p=o.geometry.attributes.position,ix=o.geometry.index,v=new THREE.Vector3();
  for(let k=0;k<(ix?.count??p.count);k+=3){
    const t=[];
    for(let j=0;j<3;j++)t.push(v.fromBufferAttribute(p,ix?ix.getX(k+j):k+j).applyMatrix4(o.matrixWorld).toArray());
    if(t.every(a=>Math.abs(a[1]-1.0893750190734863)<.00002&&a[0]>=-.52001&&a[0]<=.52001&&a[2]>=1.07999&&a[2]<=1.44001))footTriangles.push(t);
  }
});
assert.equal(footTriangles.length,2,'exact original physical footplate upper triangles');
function onFootplate(x,z){return footTriangles.some(t=>{
  const [a,b,c]=t,u=[b[0]-a[0],b[2]-a[2]],v=[c[0]-a[0],c[2]-a[2]],p=[x-a[0],z-a[2]];
  const den=u[0]*v[1]-u[1]*v[0],s=(p[0]*v[1]-p[1]*v[0])/den,q=(u[0]*p[1]-u[1]*p[0])/den;
  return s>=-.0005&&q>=-.0005&&s+q<=1.0005;
});}
const report={scope:'Actual pinned GLTFLoader/MeshoptDecoder and Three AnimationMixer; geometry only, no WebGL/image/world PASS',actual_vehicle:{file:fileURLToPath(vehicleURL),sha256:vehicleSHA,actual_footplate_upper_triangles:footTriangles},runs:[],passed:false};
for (const web of [false,true]) for (let lod=0;lod<4;lod++) {
  const path=new URL(`assets/humans/${web?'web/':''}anonymous_working_driver_1904.lod${lod}.glb`,here);
  const bytes=await fs.readFile(path);
  const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const gltf=await loader.parseAsync(geometryOnly(bytes),'');
  const expectedClips=['idle','sit_drive','walk'];
  // Active derivatives add looking; the original clips remain on every LOD.
  if(lod===0||lod===3)expectedClips.push('sit_drive_look_v2');
  assert.deepEqual(gltf.animations.map(a=>a.name).sort(),expectedClips.sort());
  const mixer=new THREE.AnimationMixer(gltf.scene),clip=gltf.animations.find(a=>a.name==='sit_drive');
  mixer.clipAction(clip).play();
  const runs=[];
  for (const time of [0,.5,.999999,1,1.5]) {
    mixer.setTime(time);gltf.scene.updateMatrixWorld(true);
    gltf.scene.traverse(o=>{if(o.isSkinnedMesh)o.skeleton.update();});
    if(!web&&lod===0&&time===.5){
      report.actual_palm_endpoints=[];
      const body=gltf.scene.getObjectByName('anonymous_working_driver_1904_body_0_lod0');
      assert(body?.isSkinnedMesh);
      const p=body.geometry.attributes.position,ix=body.geometry.index;
      for(const side of ['l','r']){
        const socket=gltf.scene.getObjectByName(`socket_hand_${side}`);assert(socket);
        const point=new THREE.Vector3().setFromMatrixPosition(socket.matrixWorld);
        const outward=new THREE.Vector3(0,0,1).transformDirection(socket.matrixWorld);
        let best=null;
        const a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3(),normal=new THREE.Vector3(),at=new THREE.Vector3(),center=new THREE.Vector3();
        const tri=new THREE.Triangle(a,b,c);
        for(let k=0;k<(ix?.count??p.count);k+=3){
          const ids=[0,1,2].map(j=>ix?ix.getX(k+j):k+j);
          for(const[j,v]of[a,b,c].entries())body.getVertexPosition(ids[j],v).applyMatrix4(body.matrixWorld);
          tri.getMidpoint(center);if(center.distanceTo(point)>.075)continue;
          tri.getNormal(normal);if(normal.dot(outward)<.1)continue;
          tri.closestPointToPoint(point,at);const distance=at.distanceTo(point);
          if(!best||distance<best.socket_distance_m)best={side,actual_body_mesh:body.name,triangle_vertex_indices:ids,endpoint_vehicle_local_m:at.toArray(),surface_normal_vehicle_local:normal.toArray(),socket_vehicle_local_m:point.toArray(),socket_distance_m:distance,clip:'sit_drive',time:.5,closed_finger_grasp_verified:false};
        }
        assert(best&&best.socket_distance_m<.03,'actual outward-facing palm surface near hand socket');
        report.actual_palm_endpoints.push(best);
      }
    }
    const min=[Infinity,Infinity], max=[-Infinity,-Infinity], count=[0,0];
    let nearSeatMin=Infinity,cushionInsideVertices=0,vertices=0;
    gltf.scene.traverse(o=>{
      if(!o.isSkinnedMesh)return;
      const p=o.geometry.attributes.position,v=new THREE.Vector3();vertices+=p.count;
      for(let i=0;i<p.count;i++) {
        o.getVertexPosition(i,v).applyMatrix4(o.matrixWorld);
        assert(Number.isFinite(v.x)&&Number.isFinite(v.y)&&Number.isFinite(v.z));
        if(o.name.includes('closed_shoes')) {
          const k=v.x>0?1:0;min[k]=Math.min(min[k],v.y);max[k]=Math.max(max[k],v.y);count[k]++;
          assert(onFootplate(v.x,v.z),'complete shoe vertices project onto actual physical footplate triangles');
        }
        if(o.name.includes('body_')||o.name.includes('trousers_')) {
          if(Math.abs(v.x)<.5&&v.z>.59&&v.z<.93&&v.y>1.695&&v.y<1.76485)cushionInsideVertices++;
          if(Math.abs(v.x)<.18&&v.z>.83&&v.z<.93&&v.y>1.7&&v.y<1.9)nearSeatMin=Math.min(nearSeatMin,v.y);
        }
      }
    });
    assert(count.every(n=>n>=3),`actual shoe surface missing: ${JSON.stringify({web,lod,count})}`);
    for(const y of min)assert(Math.abs(y-1.0893750190734863)<.0005,'actual sole footboard plane');
    assert.equal(cushionInsideVertices,0,'no actual body/trouser vertex inside central cushion volume');
    assert(nearSeatMin>=1.76485&&nearSeatMin<=1.77785,'actual near-seat surface within12mm; coarse LOD support disclosed');
    runs.push({time,vertices,sole_min_y:min,near_seat_min_y:nearSeatMin,cushion_inside_vertices:cushionInsideVertices});
  }
  // Source pose is constant. The real Mixer must preserve every sampled contact
  // across its loop boundary, rather than following a proxy pelvis point.
  assert(runs.every(r=>Math.abs(r.sole_min_y[0]-runs[0].sole_min_y[0])<1e-9));
  mixer.stopAllAction();mixer.uncacheRoot(gltf.scene);
  gltf.scene.traverse(o=>{o.geometry?.dispose();if(Array.isArray(o.material))o.material.forEach(m=>m.dispose());else o.material?.dispose();});
  report.runs.push({web,lod,file:fileURLToPath(path),samples:runs,passed:true});
}
report.passed=true;
vehicle.scene.traverse(o=>{o.geometry?.dispose();if(Array.isArray(o.material))o.material.forEach(m=>m.dispose());else o.material?.dispose();});
if(process.argv.length>2) { assert.equal(process.argv[2],'--report'); assert.equal(process.argv.length,4); await fs.writeFile(process.argv[3],JSON.stringify(report,null,2)+'\n'); }
console.log(JSON.stringify({passed:true,runs:report.runs.length,actual_mixer_samples:report.runs.reduce((n,r)=>n+r.samples.length,0),scope:report.scope}));
