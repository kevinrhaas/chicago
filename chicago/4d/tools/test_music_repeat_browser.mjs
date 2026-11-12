// Natural media endings on actual immutable R2 music. Seeking near the end
// accelerates the test; no synthetic ended event or scheduler tick advances it.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const catalog=JSON.parse(await fs.readFile(path.join(root,'renderers/web/audio/catalog.json'),'utf8'));
const policy=JSON.parse(await fs.readFile(path.join(root,'tools/audio-hosting.json'),'utf8'));
for(const a of catalog.assets.filter(a=>a.kind==='music'))for(const k of ['opus','aac'])
 a[k]=new URL(`media/${a.delivery[k].sha256}${path.extname(a[k])}`,policy.public_base).href;
let pw;try{pw=await import('playwright');}catch{pw=await import(path.join(process.env.NODE_PATH,'playwright/index.mjs'));}
const fixture=`<!doctype html><button id="on">Sound on</button><script type="module">
import {createRecordedAudio} from '/recorded-audio.js';
const catalog=${JSON.stringify(catalog)};
window.players=[];window.endings=0;window.year='1835';window.forceAAC=false;window.enabled=true;
window.sync=()=>engine.sync({active:enabled,ambienceOn:false,musicOn:true,musicLevel:1,year});
window.peak=()=>{const a=new Float32Array(meter.fftSize);meter.getFloatTimeDomainData(a);return Math.max(...a.map(Math.abs));};
document.getElementById('on').onclick=()=>{
 window.ctx=new AudioContext();ctx.resume();const music=ctx.createGain();window.meter=ctx.createAnalyser();music.connect(meter);meter.connect(ctx.destination);
 window.engine=createRecordedAudio({ctx,ambience:ctx.createGain(),music,
 media:()=>{const a=new Audio();if(forceAAC)a.canPlayType=()=>'';players.push(a);window.player=a;a.addEventListener('ended',()=>endings++);return a;},
 fetcher:(url,opts)=>String(url).endsWith('catalog.json')?Promise.resolve({ok:true,json:async()=>catalog}):fetch(url,opts)});
 sync();
};
</script>`;
const p=process.env.HTTPS_PROXY||process.env.HTTP_PROXY||process.env.https_proxy||process.env.http_proxy;
const u=p?new URL(p):null,proxy=u?{server:u.origin,...(u.username?{username:decodeURIComponent(u.username),password:decodeURIComponent(u.password)}:{})}:undefined;
const browser=await pw.chromium.launch({proxy,executablePath:process.env.PW_EXECUTABLE??'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
try{
 for(const width of [390,1280]){
  const page=await browser.newPage({viewport:{width,height:width===390?780:800}}),errors=[],requests=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().startsWith(policy.public_base))requests.push(r.url());});
  await page.route(policy.origin+'/**',async route=>{
   const name=new URL(route.request().url()).pathname.slice(1);
   if(name==='fixture')return route.fulfill({contentType:'text/html',body:fixture});
   if(['recorded-audio.js','habitat-audio.js','transport-audio.js','habitat-seasons.js','hoof-contact-events.js','work-audio.js'].includes(name))return route.fulfill({contentType:'text/javascript',body:await fs.readFile(path.join(root,'renderers/web/js',name),'utf8')});
   return route.fulfill({status:404});
  });
  await page.goto(policy.origin+'/fixture');assert.equal(requests.length,0);await page.click('#on');
  for(const year of ['1835','1812','1904']){
   if(year!=='1835')await page.evaluate(y=>{window.year=y;sync();},year);
   // T-3569: 1904 is shuffled from a random start; other eras play in catalogue order.
   const list=catalog.assets.filter(a=>a.kind==='music'&&a.era===year&&a.runtime_enabled!==false);
   const shuffled=(catalog.music_shuffle_eras??[]).includes(year),titles=list.map(a=>a.title);
   await page.waitForFunction(titles=>titles.includes(engine.state.track)&&!player.paused&&Number.isFinite(player.duration)&&peak()>1e-6,shuffled?titles:[titles[0]],{timeout:45000});
   const made=await page.evaluate(()=>players.length),heard=[await page.evaluate(()=>engine.state.track)];
   for(let i=1;i<=list.length;i++){
    const ended=await page.evaluate(()=>{player.currentTime=player.duration-.12;return endings;});
    await page.waitForFunction(({titles,prev,ended})=>endings>ended&&engine.state.track!==prev&&titles.includes(engine.state.track)&&!player.paused&&Number.isFinite(player.duration)&&player.currentTime>0&&peak()>1e-6,{titles:shuffled?titles:[titles[i%list.length]],prev:heard.at(-1),ended},{timeout:45000,polling:50});
    heard.push(await page.evaluate(()=>engine.state.track));
    assert.equal(await page.evaluate(()=>players.length),made,'reuse one unlocked streaming element through playlist wrap');
   }
   if(shuffled)assert.equal(new Set(heard.slice(0,list.length)).size,list.length,'every shuffled track plays once before any repeats');
   assert.deepEqual(await page.evaluate(()=>engine.state.errors),[]);
   console.log(`MUSIC REPEAT PASS ${width}px ${year}: natural ended events, all ${list.length} era tracks and wrap, one player, nonzero audio, no second gesture or timer tick`);
  }
  // Force the AAC selection path, including the 1835 wrap, on the same browser.
  await page.evaluate(()=>{forceAAC=true;year='1835';sync();});
  const border=catalog.assets.filter(a=>a.kind==='music'&&a.era==='1835');
  for(let i=0;i<3;i++){
   await page.waitForFunction(title=>engine.state.track===title&&player.src.endsWith('.m4a')&&!player.paused&&Number.isFinite(player.duration)&&peak()>1e-6,border[i%2].title,{timeout:45000});
   if(i<2){const ended=await page.evaluate(()=>{player.currentTime=player.duration-.12;return endings;});await page.waitForFunction(n=>endings>n,ended,{timeout:45000});}
  }
  await page.evaluate(()=>{window.stale=player.onended;enabled=false;sync();stale();});
  assert(await page.evaluate(()=>!engine.state.playing&&!player.hasAttribute('src')));
  assert.deepEqual(errors,[]);await page.evaluate(()=>{engine.dispose();ctx.close();});await page.close();
  console.log(`MUSIC AAC/MUTE PASS ${width}px: both Border tracks repeat; retired end cannot unmute`);
 }
}finally{await browser.close();}
