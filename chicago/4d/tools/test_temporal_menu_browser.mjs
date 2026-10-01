// Published front-door and cross-page appearance regression, desktop and mobile.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const {chromium}=await import(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright/index.mjs'));
const root=path.resolve('../../site/4d');
const out=process.env.MENU_SCREENSHOTS || '/tmp/t1768-browser';fs.mkdirSync(out,{recursive:true});
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
  assert(await page.locator('[data-year="1812"]').innerText().then(t=>t.includes('RECONSTRUCTION PENDING')));
  for(const skin of ['scifi','steampunk','spaceage']){
   await page.locator('#skin-choice').selectOption(skin);
   assert.equal(await page.locator('html').getAttribute('data-skin'),skin);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'horizontal overflow');
   await page.screenshot({path:`${out}/${skin}-${width}.png`,fullPage:true});
  }
  // Persist, then navigate without waiting for the entire town's heavy data.
  await page.reload();assert.equal(await page.locator('html').getAttribute('data-skin'),'spaceage');
  await page.locator('[data-year="1835"]').click();await page.waitForURL('**/4d/1835/');
  await page.locator('.gate-card .skin-tools select').waitFor();assert.equal(await page.locator('html').getAttribute('data-skin'),'spaceage');
  assert.equal(await page.locator('.gate-card .skin-tools a').getAttribute('href'),origin+'/4d/');
  await page.locator('.gate-card .skin-tools select').selectOption('steampunk');
  await page.locator('.gate-card .skin-tools a').click();await page.waitForURL('**/4d/');assert.equal(await page.locator('#skin-choice').inputValue(),'steampunk');
  // Dev preview remains within its own prefix.
  await page.goto(origin+'/4d/dev/');await page.locator('[data-year="1904"]').click();await page.waitForURL('**/4d/dev/1904/');
  await page.goto(origin+'/4d/1812/');assert(await page.getByText('Reconstruction pending',{exact:true}).isVisible());
  // Explicit old root links keep query and fragment.
  await page.goto(origin+'/4d/?year=1904&structure=glessner_house#evidence');await page.waitForURL('**/4d/1904/?year=1904&structure=glessner_house#evidence');
  assert.equal(errors.length,0,errors.join('\n'));
  console.log(`PASS ${width}: three periods, three skins, persistence, transfer, home return, dev path, deep link, containment, no JS errors`);
  await context.close();
 }
 const context=await browser.newContext({javaScriptEnabled:false});const page=await context.newPage();await page.goto(origin+'/4d/');assert.equal(await page.locator('.era').count(),3);assert(await page.locator('[data-year="1835"]').isVisible());await context.close();console.log('PASS no-JavaScript: all destination links visible');
}finally{await browser.close();await new Promise(r=>server.close(r));}
