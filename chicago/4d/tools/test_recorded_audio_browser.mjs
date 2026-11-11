// T-3532: real browser playback and codec checks, independent of the costly 3D boot.
// NODE_PATH=/path/to/node_modules PW_EXECUTABLE=/usr/bin/chromium node tools/test_recorded_audio_browser.mjs
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../renderers/web');
const catalog=JSON.parse(await fs.readFile(path.join(root,'audio/catalog.json'),'utf8'));
const deliveries=catalog.assets.reduce((n,a)=>n+(a.kind==='music'?2:1),0);
let pw;try{pw=await import('playwright');}catch{pw=await import(path.join(process.env.NODE_PATH,'playwright/index.mjs'));}
const fixture=`<!doctype html><button id="on">Enable audio</button><script type="module">
import {createSound} from '/js/sound.js';
let ctx;window.year='1835';window.season='summer';window.levels={soundMaster:0,soundAmbience:1,soundMusic:.4};
window.sound=createSound({audio:()=>ctx,settings:()=>levels,scene:()=>year,
environment:()=>({season,camera:{position:{x:0,y:2,z:0}},terrain:{loaded:false}})});
document.getElementById('on').onclick=()=>{ctx??=new AudioContext();ctx.resume();levels.soundMaster=1;sound.sync();};
</script>`;
const server=http.createServer(async(req,res)=>{
 try{
  const url=new URL(req.url,'http://localhost');if(url.pathname==='/fixture'){res.setHeader('Content-Type','text/html');res.end(fixture);return;}
  const file=path.resolve(root,'.'+decodeURIComponent(url.pathname));if(!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
  const data=await fs.readFile(file);res.setHeader('Content-Type',({'.js':'text/javascript','.json':'application/json','.html':'text/html','.ogg':'audio/ogg','.m4a':'audio/mp4','.mp3':'audio/mpeg'})[path.extname(file)]??'application/octet-stream');
  const match=/bytes=(\d+)-(\d*)/.exec(req.headers.range??'');
  if(match){const start=Number(match[1]),end=match[2]?Math.min(Number(match[2]),data.length-1):data.length-1;res.writeHead(206,{'Content-Range':`bytes ${start}-${end}/${data.length}`,'Accept-Ranges':'bytes','Content-Length':end-start+1});res.end(data.subarray(start,end+1));}
  else{res.setHeader('Content-Length',data.length);res.end(data);}
 }catch{res.writeHead(404);res.end();}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const base=`http://127.0.0.1:${server.address().port}`;
const browser=await pw.chromium.launch({executablePath:process.env.PW_EXECUTABLE??'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
try{
 for(const width of [390,1280]){
  const page=await browser.newPage({viewport:{width,height:width===390?780:800}});const errors=[],audioRequests=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().includes('/audio/'))audioRequests.push(r.url());});
  await page.goto(base+'/fixture');await page.waitForFunction(()=>!!window.sound);await page.waitForTimeout(300);
  assert.equal(audioRequests.length,0,'muted initial state is fetch-free');await page.click('#on');
  await page.waitForFunction(()=>sound.state.recorded?.playing&&sound.state.recorded?.track==='Border Ballad');
  await page.waitForFunction(()=>sound.state.recorded?.voices.includes('wind'));
  assert(await page.evaluate(()=>sound.state.recorded.decodedBytes>0&&sound.state.recorded.decodedBytes<14*1024*1024));
  await page.evaluate(()=>{season='winter';sound.sync();});
  assert(await page.evaluate(()=>!sound.state.recorded.voices.includes('wind')),'winter stops leafy wind');
  assert(!audioRequests.some(u=>u.includes('/1812/')||u.includes('/1904/')),'only selected era requested');
  await page.evaluate(()=>{year='1812';sound.sync();});await page.waitForFunction(()=>sound.state.recorded?.track==='Reel of the Frontier'&&sound.state.recorded?.playing);
  await page.evaluate(()=>{year='1904';sound.sync();});await page.waitForFunction(()=>sound.state.recorded?.track==='Salon Waltz'&&sound.state.recorded?.playing);
  await page.evaluate(()=>{levels.soundMusic=0;sound.sync();});assert.equal(await page.evaluate(()=>sound.state.recorded.playing),false);
  assert(!audioRequests.some(u=>u.includes('/candidates/')),'no candidate media is scheduled without qualified habitat context');
  await page.evaluate(()=>{levels.soundMusic=.4;sound.sync();});await page.waitForFunction(()=>sound.state.recorded?.playing);
  await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'));});
  assert(await page.evaluate(()=>sound.state.silent&&!sound.state.recorded.playing));
  await page.evaluate(()=>{delete document.hidden;levels.soundMaster=0;sound.sync();});
  const count=audioRequests.length;await page.waitForTimeout(400);assert.equal(audioRequests.length,count,'mute does not restart requests');
  await page.evaluate(()=>sound.dispose());
  await page.goto(base+'/audio/credits.html');await page.waitForSelector('article');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  for(const [era,n] of [['1812',3],['1835',2],['1904',2]]){await page.selectOption('#era',era);assert.equal(await page.locator('article').count(),n);}
  await page.selectOption('#era','candidate');assert.equal(await page.locator('article').count(),catalog.assets.filter(a=>a.kind==='candidate'&&!a.runtime_enabled).length);
  await page.selectOption('#era','habitat');assert.equal(await page.locator('article').count(),3);
  await page.selectOption('#era','transport');assert.equal(await page.locator('article').count(),2);
  await page.selectOption('#era','environment');
  const approvedCard=page.locator('article').filter({has:page.getByRole('heading',{name:'Light water on rocks',exact:true})});
  assert.equal(await approvedCard.count(),1);
  assert.equal(await approvedCard.locator('small').textContent(),'Shared · Environment · reconstructed proxy');
  assert((await approvedCard.textContent()).includes('Owner selected'));
  assert(!(await approvedCard.locator('small').textContent()).includes('Held'));
  const heldCard=page.locator('article').filter({has:page.getByRole('heading',{name:'Previous river recording (held)',exact:true})});
  assert.equal(await heldCard.count(),1);
  assert.equal(await heldCard.locator('small').textContent(),'Held from scene playback');
  await page.click('#era');
  const decode=await page.evaluate(async()=>{
   const c=await(await fetch('./catalog.json')).json(),ctx=new AudioContext();await ctx.resume();const rows=[];
   for(const a of c.assets)for(const file of a.kind==='music'?[a.opus,a.aac]:[a.url]){
    const bytes=await(await fetch(file)).arrayBuffer();let timer;
    const b=await Promise.race([ctx.decodeAudioData(bytes),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('decode timeout: '+file)),60000);})]);clearTimeout(timer);
    rows.push({file,duration:b.duration,expected:a.duration_s,channels:b.numberOfChannels,environment:a.kind==='environment',candidate:a.kind==='candidate'});
   }await ctx.close();return rows;
  });
  assert.equal(decode.length,deliveries);assert(decode.every(r=>r.duration>0&&Math.abs(r.duration-r.expected)<.2),'actual decoded durations match catalogue');
  assert(decode.filter(r=>r.candidate).every(r=>r.channels===1&&r.duration<=24.1),'candidate auditions are bounded mono clips');
  assert(decode.filter(r=>r.environment).every(r=>Math.abs(r.duration-22)<.05&&r.channels===1),'environment delivers 22-second mono loops');assert.deepEqual(errors,[]);
  console.log(`AUDIO BROWSER PASS — ${width}px: no muted requests; correct era streams; recorded environment and winter suppression; music/mute/hidden cleanup; ${deliveries} codec deliveries decode; candidates remain unscheduled; library filters and fit`);
  await page.close();
 }
}finally{await browser.close();await new Promise(r=>server.close(r));}
