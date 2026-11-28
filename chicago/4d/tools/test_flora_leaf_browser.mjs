#!/usr/bin/env node
// T-3748: compile the real flora material and geometry. The local test server
// exposes private factories; it changes no product exports or renderer code.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import {createRequire} from 'node:module';
const root=path.resolve(new URL('..',import.meta.url).pathname);
const {chromium}=createRequire(import.meta.url)('playwright');
const exports=['plantMaterial','tuftGeometry','forbGeometry','cardGeometry','spikeGeometry','spireGeometry',
  'panicleGeometry','rayGeometry','pompomGeometry','domeGeometry','corymbGeometry','compoundGeometry'];
const server=http.createServer((req,res)=>{
  const pathname=req.url.split('?')[0];
  if(pathname==='/') {
    res.setHeader('Content-Type','text/html');
    res.end('<link rel="icon" href="data:,"><script type="importmap">{"imports":{"three":"/vendor/three-0.185.1/three.module.js","three/addons/":"/vendor/three-0.185.1/addons/"}}</script>');return;
  }
  const file=path.join(root,'renderers/web',pathname);
  if(!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':'application/octet-stream');
  if(pathname==='/js/flora.js')res.end(fs.readFileSync(file,'utf8')+'\nexport { '+exports.join(',')+' };\n');
  else fs.createReadStream(file).pipe(res);
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE||undefined,
  args:['--no-sandbox','--enable-unsafe-swiftshader']});
try {
  const page=await browser.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
  const result=await page.evaluate(async()=>{
    const THREE=await import('three'),flora=await import('/js/flora.js');
    const {NEAR_FETCH_GLSL}=await import('/js/flora-gpu-near.js');
    const {foliageAtlas}=await import('/js/foliage-atlas.js');
    const {applySeasonLook,patchFoliage,FOLIAGE}=await import('/js/season.js');
    const atlas=foliageAtlas();
    const renderer=new THREE.WebGLRenderer();renderer.setSize(96,96);
    const target=new THREE.WebGLRenderTarget(96,96);
    const scene=new THREE.Scene();scene.background=new THREE.Color(0);
    const sun=new THREE.DirectionalLight(0xffffff,2);sun.position.set(4,5,3);scene.add(sun);
    scene.add(new THREE.HemisphereLight(0xcce2ff,0x403b2c,.6));
    const camera=new THREE.PerspectiveCamera(48,1,.1,30);camera.position.set(2,1.8,3);camera.lookAt(0,.65,0);
    const uniforms={uChiTime:{value:0},uChiWind:{value:new THREE.Vector2(.82,.57)},uChiSway:{value:.15},
      uChiWaveK:{value:1},uChiSun:{value:new THREE.Vector3(4,5,3).normalize()},
      uChiSunCol:{value:new THREE.Vector3(.9,.8,.7)},uChiSky:{value:new THREE.Vector3(.025,.03,.04)},uChiFoliage:{value:atlas}};
    const tex=values=>{
      const t=new THREE.DataTexture(new Float32Array(values),1,1,THREE.RGBAFormat,THREE.FloatType);
      t.needsUpdate=true;return t;
    };
    const transforms=[2,1.8,.35,.72],ring=[10000,1,0,0];
    const fetchTextures=[tex([0,0,0,6]),tex(transforms),tex([1,1,1,.5]),tex(ring)];
    const gpuNear={glsl:NEAR_FETCH_GLSL,uniforms:Object.fromEntries(fetchTextures.map((t,i)=>['uNearI'+i,{value:t}]))};
    gpuNear.uniforms.uNearW={value:1};
    function mesh(source,{gpu=false,billboard=false}={}) {
      const g=new THREE.InstancedBufferGeometry().copy(source);g.instanceCount=1;
      g.setAttribute('aFlora',new THREE.InstancedBufferAttribute(new Float32Array(transforms),4));
      g.setAttribute('aChiRing',new THREE.InstancedBufferAttribute(new Float32Array(ring),4));
      g.setAttribute('aChiFamily',new THREE.InstancedBufferAttribute(new Float32Array([0]),1));
      const material=flora.plantMaterial({uniforms,billboard,gpuNear:gpu?gpuNear:null});
      patchFoliage(material,FOLIAGE.grass);
      const o=gpu?new THREE.Mesh(g,material):new THREE.InstancedMesh(g,material,1);
      o.frustumCulled=false;return o;
    }
    function read(o) {
      scene.add(o);renderer.setRenderTarget(target);renderer.render(scene,camera);
      const pixels=new Uint8Array(96*96*4);renderer.readRenderTargetPixels(target,0,0,96,96,pixels);scene.remove(o);
      let lit=0,energy=0;
      for(let i=0;i<pixels.length;i+=4) {const v=pixels[i]+pixels[i+1]+pixels[i+2];energy+=v;if(v>3)lit++;}
      return {pixels,lit,energy};
    }
    const source=flora.tuftGeometry(9,4),cpu=mesh(source),gpu=mesh(source,{gpu:true}),parity=[];
    applySeasonLook('summer');
    for(const time of [0,2.3,9]) {
      uniforms.uChiTime.value=time;const a=read(cpu),b=read(gpu);
      const delta=a.pixels.reduce((sum,v,i)=>sum+Math.abs(v-b.pixels[i]),0)/a.pixels.length;
      parity.push({time,cpuLit:a.lit,gpuLit:b.lit,delta});
    }
    for(const o of [cpu,gpu]){o.geometry.dispose();o.material.dispose();}source.dispose();
    const surfaces=[];
    for(const [name,source,billboard] of [['forb',flora.forbGeometry(3),false],['card',flora.cardGeometry(7),true]]) {
      const o=mesh(source,{billboard}),counts={};
      for(const season of ['spring','summer','fall','winter']){applySeasonLook(season);const a=read(o);counts[season]=a.lit;}
      surfaces.push({name,counts});o.geometry.dispose();o.material.dispose();source.dispose();
    }
    const heads=[];
    camera.position.set(4,3,6);camera.lookAt(0,2,0);
    for(const name of ['spike','spire','panicle','ray','pompom','dome','corymb','compound']) {
      const source=flora[name+'Geometry'](false),o=mesh(source),counts={};
      for(const season of ['summer','spring','winter']){applySeasonLook(season);counts[season]=read(o).lit;}
      heads.push({name,counts});o.geometry.dispose();o.material.dispose();source.dispose();
    }
    const runnable=renderer.info.programs.every(p=>p.diagnostics?.runnable!==false);
    for(const t of fetchTextures)t.dispose();atlas.dispose();target.dispose();renderer.dispose();applySeasonLook('summer');
    return {parity,surfaces,heads,runnable};
  });
  assert(result.runnable&&!errors.length,errors.join('\n'));
  for(const r of result.parity)assert(r.cpuLit>30&&r.gpuLit>30&&r.delta<.1,JSON.stringify(r));
  for(const r of result.surfaces)assert(Object.values(r.counts).every(n=>n>0),JSON.stringify(r));
  for(const r of result.heads)assert(r.counts.summer>0&&r.counts.spring===0&&r.counts.winter>0,JSON.stringify(r));
  console.log('PASS real flora GLSL: CPU/fetched wind parity, folded broad leaves, camera-facing cards and seasonal flower withholding',JSON.stringify(result));
} finally {await browser.close();server.close();}
