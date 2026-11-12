// T-3532: test the generated app modules against real R2 media and browser CORS.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../../site/4d/walk');
let pw;try{pw=await import('playwright');}catch{pw=await import(path.join(process.env.NODE_PATH,'playwright/index.mjs'));}
const catalog=JSON.parse(await fs.readFile(path.join(root,'audio/catalog.json'),'utf8'));
const origin='https://chicago.polecat.live';
const fixture=`<!doctype html><button id="on">Sound on</button><script type="module">
import {createSound} from '/js/sound.js';let ctx;window.year='1835';window.season='summer';
window.levels={soundMaster:0,soundAmbience:1,soundMusic:.4};
window.sound=createSound({audio:()=>ctx,settings:()=>levels,scene:()=>year,
environment:()=>({season,camera:{position:{x:0,y:2,z:0}},terrain:{loaded:false}})});
document.getElementById('on').onclick=()=>{ctx??=new AudioContext();ctx.resume();levels.soundMaster=.8;sound.sync();};
</script>`;
const proxyURL=process.env.HTTPS_PROXY||process.env.HTTP_PROXY||process.env.https_proxy||process.env.http_proxy;
const proxyAddress=proxyURL?new URL(proxyURL):null;
const proxy=proxyAddress?{server:proxyAddress.origin,...(proxyAddress.username?{username:decodeURIComponent(proxyAddress.username),password:decodeURIComponent(proxyAddress.password)}:{})}:undefined;
const browser=await pw.chromium.launch({proxy,executablePath:process.env.PW_EXECUTABLE??'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
try{
 for(const width of [390,1280]){
  const page=await browser.newPage({viewport:{width,height:780}}),requests=[],errors=[];
  await page.route(origin+'/**',async route=>{
   const url=new URL(route.request().url());
   if(url.pathname==='/fixture'){await route.fulfill({contentType:'text/html',body:fixture});return;}
   const file=path.resolve(root,'.'+decodeURIComponent(url.pathname));
   if(!file.startsWith(root+path.sep)){await route.abort();return;}
   try{await route.fulfill({body:await fs.readFile(file),contentType:({'.js':'text/javascript','.json':'application/json','.html':'text/html','.css':'text/css'})[path.extname(file)]??'application/octet-stream'});}
   catch{await route.fulfill({status:404,body:'Not found'});}
  });
  page.on('request',r=>{if(r.url().startsWith(catalog.hosting.public_base))requests.push(r.url());});
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(origin+'/fixture');await page.waitForFunction(()=>!!window.sound);await page.waitForTimeout(300);
  assert.equal(requests.length,0);await page.click('#on');
  await page.waitForFunction(()=>sound.state.recorded?.playing&&sound.state.recorded.voices.includes('wind'),{},{timeout:30000});
  assert.equal(await page.evaluate(()=>sound.state.recorded.track),'Border Ballad');
  for(const [era,title] of [['1812','Reel of the Frontier'],['1904','Salon Waltz']]){
   await page.evaluate(era=>{year=era;sound.sync();},era);
   await page.waitForFunction(title=>sound.state.recorded?.playing&&sound.state.recorded.track===title,title);
  }
  assert(requests.every(u=>/^https:\/\/[^/]+\/media\/[a-f0-9]{64}\.(ogg|m4a|mp3)$/.test(u)));
  const candidateURLs=new Set(catalog.assets.filter(a=>a.kind==='candidate').map(a=>a.url));
  assert(!requests.some(u=>candidateURLs.has(u)));
  await page.evaluate(()=>{levels.soundMaster=0;sound.sync();});
  assert(await page.evaluate(()=>sound.state.silent&&!sound.state.recorded.playing&&sound.state.recorded.decodedBytes===0));
  await page.evaluate(()=>sound.dispose());
  await page.goto(origin+'/audio/credits.html');await page.waitForSelector('article');
  await page.selectOption('#era','candidate');assert.equal(await page.locator('article').count(),13);
  await page.selectOption('#era','habitat');assert.equal(await page.locator('article').count(),6);
  await page.selectOption('#era','transport');assert.equal(await page.locator('article').count(),3);
  assert((await page.locator('article small').allTextContents()).every(t=>t.includes('Moving team')&&t.includes('reconstructed proxy')));
  await page.selectOption('#era','work'); assert.equal(await page.locator('article').count(),1);
  assert((await page.locator('article small').innerText()).includes('1812 · Visible work'));
  await page.selectOption('#era','1812'); assert.equal(await page.locator('article').count(),16);
  assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth));
  assert.deepEqual(errors,[]);
  console.log(`HOSTED AUDIO BROWSER PASS ${width}px: published modules, real R2 music/decoded wind, era changes, mute cleanup, no candidate autoplay, catalogue layout`);
  await page.close();
 }
}finally{await browser.close();}
