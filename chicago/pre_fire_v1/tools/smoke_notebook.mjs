/** Exercise the published field notebook, navigation and evidence exports. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const { chromium } = createRequire(import.meta.url)('playwright');
const ROOT = path.resolve(process.env.SMOKE_ROOT || fileURLToPath(new URL('../../../site/', import.meta.url)));
const mime = { '.html':'text/html', '.js':'text/javascript', '.css':'text/css', '.json':'application/json', '.csv':'text/csv', '.jpg':'image/jpeg' };
const server = http.createServer((req,res) => {
  let file;
  try { file = path.resolve(ROOT, '.' + decodeURIComponent(new URL(req.url,'http://local').pathname)); }
  catch { res.writeHead(400).end(); return; }
  if (!file.startsWith(ROOT + path.sep)) { res.writeHead(403).end(); return; }
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404).end(); return; }
  res.writeHead(200, { 'content-type':mime[path.extname(file)] || 'application/octet-stream' }); fs.createReadStream(file).pipe(res);
});
await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
const origin = `http://127.0.0.1:${server.address().port}`, base = origin + '/pre-fire/viewer/';
let browser, passed = 0;
const check = (ok,text) => { assert.ok(ok,text); passed++; console.log('PASS ' + text); };
const model = JSON.parse(fs.readFileSync(path.join(ROOT,'pre-fire/viewer/field-notebook-1871.json'),'utf8'));
const pageMap = Object.fromEntries(model.pages.map(p => [p.id,p]));
try {
  browser = await chromium.launch({ executablePath:process.env.PW_EXECUTABLE || '/usr/bin/chromium', headless:true });
  for (const [size,viewport] of [['mobile',{width:390,height:780}],['desktop',{width:1280,height:800}]]) {
    const context = await browser.newContext({viewport}); const page = await context.newPage(); const errors = [];
    page.on('pageerror',e => errors.push(String(e)));
    page.on('response',r => { if(r.url().startsWith(origin) && r.status() >= 400) errors.push(r.status()+' '+r.url()); });
    await page.goto(base+'research.html'); await page.locator('.notebook-entry a').click(); await page.waitForSelector('.record-card');
    const cards = page.locator('.record-card');
    check(await cards.count() === model.records.length, size+': dossier opens full notebook');
    check(await page.locator('.scene-card').count() === model.scene_packets.length,size+': all scene studies render');
    check(await page.locator('.source-page').count() === model.pages.length,size+': all source pages render');
    check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1),size+': initial layout fits');
    if (process.env.SCREENSHOT_DIR) {
      fs.mkdirSync(process.env.SCREENSHOT_DIR,{recursive:true});
      await page.screenshot({path:path.join(process.env.SCREENSHOT_DIR,'notebook-'+size+'.png')});
    }
    for (const [select,key] of [['notebook-topic','topic'],['notebook-basis','evidence_type']]) {
      for (const value of [...new Set(model.records.map(r=>r[key]))]) {
        await page.locator('#'+select).selectOption(value);
        check(await cards.count() === model.records.filter(r=>r[key]===value).length,`${size}: ${key} ${value}`);
      }
      await page.locator('#'+select).selectOption('');
    }
    for (const book of model.books) {
      await page.locator('#notebook-book').selectOption(book.id);
      check(await cards.count() === model.records.filter(r=>r.source_ids.some(s=>pageMap[s].book_id===book.id)).length,size+': publication '+book.id);
    }
    await page.locator('#notebook-clear').click();
    await page.locator('#notebook-search').fill('Quincy');
    check(await page.locator('#record-hotel-palmer').isVisible(),size+': historical address search');
    await page.locator('#notebook-topic').selectOption('Buildings & addresses');
    await page.locator('#notebook-basis').selectOption('listed');
    await page.locator('#notebook-book').selectOption('edwards1871');
    const expected = model.records.filter(r => r.topic==='Buildings & addresses' && r.evidence_type==='listed' && r.source_ids.some(s=>pageMap[s].book_id==='edwards1871') && JSON.stringify(r).toLowerCase().includes('quincy')).length;
    check(await cards.count() === expected,size+': all filters combine');
    await page.reload(); await page.waitForSelector('.record-card');
    check(await cards.count()===expected && await page.locator('#notebook-search').inputValue()==='Quincy',size+': filters survive reload');
    await page.locator('#notebook-search').fill('nonexistent-record-xyz');
    check(await cards.count()===0 && await page.locator('#notebook-empty').isVisible(),size+': empty state');
    await page.locator('#notebook-clear').click();
    check(await cards.count()===model.records.length,size+': clear restores all observations');
    await page.locator('#notebook-expand').click();
    check(await page.locator('.record-card[open]').count()===model.records.length,size+': expand all');
    check((await page.locator('#record-hotel-palmer .card-body').textContent()).includes('northwest corner Quincy'),size+': finding and evidence body visible');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),size+': expanded records fit');
    await page.locator('#notebook-collapse').click();
    check(await page.locator('.record-card[open]').count()===0,size+': collapse all');
    const scene=model.scene_packets[0];
    await page.locator('#scene-'+scene.id+' > summary').click();
    await page.locator('#scene-'+scene.id+' .scene-evidence').click();
    check(await cards.count()===scene.record_ids.length,size+': scene filters its linked observations');
    check(new URL(page.url()).searchParams.get('scene')===scene.id,size+': scene filter has shareable URL');
    await page.reload();await page.waitForSelector('.record-card');
    check(await cards.count()===scene.record_ids.length,size+': scene filter survives reload');
    await page.goto(base+'notebook.html?q=missing&book=works1870&scene=state-randolph#record-hotel-palmer');
    await page.waitForSelector('#record-hotel-palmer[open]');
    check(await page.locator('#record-hotel-palmer').isVisible(),size+': observation deep link clears conflicting filters');
    await page.locator('#record-hotel-palmer a[href="#source-dir-1031"]').click();
    await page.waitForSelector('#source-dir-1031[open]');
    check(await page.locator('#source-dir-1031').isVisible(),size+': source context opens and scrolls');
    await page.waitForFunction(()=>document.querySelector('#source-dir-1031 img')?.naturalWidth>0);
    check(await page.locator('#source-dir-1031 img').getAttribute('alt') !== '',size+': local original scan loads with description');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),size+': source register fits');
    await page.goto(base+'notebook.html#scene-union-park');await page.waitForSelector('#scene-union-park[open]');
    check(await page.locator('#scene-union-park').isVisible(),size+': scene deep link opens study');
    const csv = await context.request.get(base+'field-observations-1871.csv');
    check(csv.ok() && (await csv.text()).includes('historical_location') && (await csv.text()).includes('hotel-palmer'),size+': CSV download carries evidence and dates');
    const json = await context.request.get(base+'field-notebook-1871.json');
    check(json.ok() && (await json.json()).records.length===model.records.length,size+': JSON download complete');
    for(const source of model.pages.filter(p=>p.local_image)) {
      const res=await context.request.get(new URL(source.local_image,base).href);
      check(res.ok() && (await res.body()).length===source.bytes,size+': original scan '+source.id);
    }
    check(errors.length===0,size+': no browser errors or failed local requests '+errors.join('; '));
    await context.close();
  }
  const staticContext=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:780}});
  const staticPage=await staticContext.newPage();await staticPage.goto(base+'notebook.html');
  check(await staticPage.locator('noscript a').isVisible(),'no-JavaScript route exposes reading edition');
  await staticPage.locator('noscript a').click();
  check(await staticPage.locator('#observations article').count()===model.records.length,'reading edition includes every observation without JavaScript');
  check(await staticPage.locator('#scenes article').count()===model.scene_packets.length,'reading edition includes every scene study');
  check(await staticPage.evaluate(()=>[...document.querySelectorAll('a[href^="#"]')].every(a=>document.getElementById(a.hash.slice(1)))),'reading edition has no broken fragment links');
  check(await staticPage.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'reading edition fits mobile');
  await staticContext.close();
  const failure=await browser.newContext();const failurePage=await failure.newPage();
  await failure.route('**/field-notebook-1871.json',r=>r.fulfill({status:503,body:'unavailable'}));
  await failurePage.goto(base+'notebook.html');
  await failurePage.waitForSelector('#notebook-status a[href="notebook-reading.html"]');
  check(await failurePage.locator('#notebook-status').isVisible(),'failed JSON load offers complete static edition and retry');
  await failure.close();
  console.log(`Notebook: ${passed} checks passed.`);
} finally { if(browser) await browser.close(); await new Promise(resolve=>server.close(resolve)); }
