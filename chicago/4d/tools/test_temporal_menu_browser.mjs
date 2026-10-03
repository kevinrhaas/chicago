// Published front-door and cross-page appearance regression, desktop and mobile.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
const {chromium}=await import(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES || process.env.NODE_PATH?.split(path.delimiter)[0] || execSync('npm root -g',{encoding:'utf8'}).trim(),'playwright/index.mjs'));
const root=path.resolve('../../site/4d');
const out=process.env.MENU_SCREENSHOTS || '/tmp/t2036-browser';fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'};
const server=http.createServer((req,res)=>{
 const url=new URL(req.url,'http://local');let route=decodeURIComponent(url.pathname).replace(/^\/4d\/(dev\/)?/,'/');
 let file=path.join(root,route);if(fs.existsSync(file)&&fs.statSync(file).isDirectory()) {if(!url.pathname.endsWith('/')){res.writeHead(301,{Location:url.pathname+'/'+url.search});res.end();return;}file=path.join(file,'index.html');}
 fs.readFile(file,(err,data)=>{res.writeHead(err?404:200,{'Content-Type':types[path.extname(file)]||'application/octet-stream'});res.end(err?'Not found':data);});
});await new Promise(r=>server.listen(0,'127.0.0.1',r));
const origin=`http://127.0.0.1:${server.address().port}`;
const browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE,args:['--no-sandbox','--enable-unsafe-swiftshader']});
try {
 for(const width of [1280,390]){
  const context=await browser.newContext({viewport:{width,height:width===390?844:800},reducedMotion:width===390?'reduce':'no-preference'});
  const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(origin+'/4d/');await page.waitForFunction(()=>document.querySelectorAll('.era.resolved').length===3);
  assert.equal(await page.locator('.era').count(),3);
  assert(await page.locator('[data-year="1812"]').innerText().then(t=>t.includes('SURVEY IN PROGRESS')));
  assert.equal(await page.locator('html').getAttribute('data-skin'),'control-room','the standard machine is the default');
  const dial=page.locator('.masthead .machine-dial');
  assert.equal(await page.locator('.masthead .machine-dial').count(),1,'one quiet dial, not a row of buttons');
  for(const [skin,name] of [['brass','Precision Brass'],['worlds-fair','Retro Future'],['deep-space','Deep Space'],['control-room','Control Room']]){
   await dial.click();
   assert.equal(await page.locator('html').getAttribute('data-skin'),skin);
   assert.equal(await dial.getAttribute('aria-label'),`Appearance: ${name}. Change appearance`);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'horizontal overflow');
   await page.screenshot({path:`${out}/${skin}-${width}.png`,fullPage:true});
  }
  await dial.click();await dial.click();
  assert.equal(await page.locator('html').getAttribute('data-skin'),'worlds-fair');
  assert.equal(await page.locator('html').getAttribute('data-theme'),'light','Retro Future is the light machine');
  const light = await page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--panel-solid'));
  await page.evaluate(()=>{document.documentElement.dataset.theme='dark';});
  assert.notEqual(await page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--panel-solid')),light,'the renderer light/dark switch still reskins a machine');
  await page.evaluate(()=>{document.documentElement.dataset.theme='light';});
  // Persist, then navigate without waiting for the entire town's heavy data.
  await page.reload();assert.equal(await page.locator('html').getAttribute('data-skin'),'worlds-fair');
  await page.locator('[data-year="1835"]').click();await page.waitForURL('**/4d/1835/');
  await page.locator('.gate-card .skin-tools .machine-dial').waitFor();assert.equal(await page.locator('html').getAttribute('data-skin'),'worlds-fair');
  assert.equal(await page.locator('.gate-card .skin-tools a').getAttribute('href'),origin+'/4d/');
  await page.locator('.gate-card .skin-tools .machine-dial').click();
  await page.locator('.gate-card .skin-tools a').click();await page.waitForURL('**/4d/');assert.equal(await page.locator('html').getAttribute('data-skin'),'deep-space');
  assert.equal(await page.locator('.masthead .machine-dial').getAttribute('title'),'Appearance: Deep Space');
  // A visitor who chose an earlier skin keeps it, under its new machine name.
  await page.evaluate(()=>localStorage.setItem('chicago4d.skin','steampunk'));await page.reload();assert.equal(await page.locator('html').getAttribute('data-skin'),'brass');
  // Dev preview remains within its own prefix.
  await page.goto(origin+'/4d/dev/');await page.locator('[data-year="1904"]').click();await page.waitForURL('**/4d/dev/1904/');
  await page.goto(origin+'/4d/1812/');assert(await page.getByText('Survey in progress · reconstruction pending',{exact:true}).isVisible());
  // Explicit old root links keep query and fragment.
  await page.goto(origin+'/4d/?year=1904&structure=glessner_house#evidence');await page.waitForURL('**/4d/1904/?year=1904&structure=glessner_house#evidence');
  assert.equal(errors.length,0,errors.join('\n'));
  console.log(`PASS ${width}: three coordinates, four machines, legacy migration, persistence, transfer, home return, dev path, deep link, containment, no JS errors`);
  await context.close();
 }
 const context=await browser.newContext({javaScriptEnabled:false});const page=await context.newPage();await page.goto(origin+'/4d/');assert.equal(await page.locator('.era').count(),3);assert(await page.locator('[data-year="1835"]').isVisible());await context.close();console.log('PASS no-JavaScript: all destination links visible');
}finally{await browser.close();await new Promise(r=>server.close(r));}
