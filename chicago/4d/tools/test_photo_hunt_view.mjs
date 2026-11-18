/** Real Home and hunt modules, real compiled catalogue, small image fixtures; no 3D world. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { huntOrder, HUNT_STORAGE_KEY } from '../renderers/web/js/photo-hunt.js';

const { chromium } = createRequire(import.meta.url)('playwright');
const root = path.resolve(new URL('..', import.meta.url).pathname);
const web = path.join(root, 'renderers/web');
const doc = JSON.parse(execFileSync('python3', ['-c',
  'import sys,json;sys.path.insert(0,"tools");import compile_pictures as p;print(json.dumps(p.add_place_names(p.derive(*p.read_tree()),p.load_json(p.PLACE_NAMES))["1904"]))'], { cwd: root, maxBuffer: 4 * 1024 * 1024 }));
const registry = [];
for (const id of Object.keys(doc.by_structure)) {
  const file = path.join(root, 'data/sidecars/1904', `${id}.json`);
  if (fs.existsSync(file)) registry.push([id, { sidecar: JSON.parse(fs.readFileSync(file)) }]);
}
const fixture = JSON.stringify({ doc, registry });
const pageHTML = `<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/css/photo-hunt.css"><style>
:root { --ink: #ecf0f3; --panel-raised: #252e38; --edge: #8994a1; color:var(--ink); background:#18212a; font:16px system-ui; }
body { margin:0; } #nav-home { max-width:400px; box-sizing:border-box; padding:8px; } a { color:#97d6ff; }</style></head>
<body><nav id="fixture-rail" aria-label="Navigator apps"></nav><div id="fixture-screens"><div id="nav-home"></div></div><script type="module">
import home from '/js/apps/home.js';
import { createDestinations } from '/js/destinations.js';
import { createRail } from '/js/nav-rail.js';
window.fixture = { loads:0, visits:[], blocked:false, pose:null, home, level:1 };
const context = { scene:{id:'1904'}, api:{}, navigator:{get level(){return fixture.level;}}, actions:{
 freeRoam:()=>{fixture.level=0; fixture.rail.setVisible(false); fixture.roamed=true;},
 photoHunt:{
  async load(){ fixture.loads++; const data=await fetch('/fixture.json').then(r=>r.json());
   const destinations=createDestinations({scene:{},registry:new Map(data.registry)}); destinations.addPhotos(data.doc);
   fixture.destinations=destinations; return {doc:data.doc,destinations}; },
  position:()=>fixture.pose,
  visit:(id)=>{if(fixture.blocked)return false; fixture.visits.push(id); return true;}
 } } };
fixture.context=context;
fixture.rail=createRail({rail:document.getElementById('fixture-rail'),screens:document.getElementById('fixture-screens'),
 context:()=>context, reduced:()=>true, onOpen:(_id,by)=>{
  if(by!=='quiet'&&fixture.level===0){fixture.level=1;fixture.rail.setVisible(true);}
 }});
fixture.rail.register(home);
fixture.rail.register({id:'other',label:'Other app',mount(el){el.textContent='Another Navigator app';}});
fixture.rail.evaluate(); await fixture.rail.select('home');
Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(new Error('denied'))},configurable:true});
</script></body></html>`;
const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, 'http://localhost').pathname;
  if (pathname === '/' || pathname === '/1904/') { res.setHeader('Content-Type', 'text/html'); res.end(pageHTML); return; }
  if (pathname === '/fixture.json') { res.setHeader('Content-Type', 'application/json'); res.end(fixture); return; }
  const file = path.resolve(web, `.${pathname}`);
  if (!file.startsWith(`${web}/`)) { res.writeHead(403); res.end(); return; }
  fs.readFile(file, (error, bytes) => { res.writeHead(error ? 404 : 200, { 'Content-Type': file.endsWith('.js') ? 'text/javascript' : 'text/css' }); res.end(error ? '' : bytes); });
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || '/usr/bin/chromium', args: ['--no-sandbox'] });
const report = { kind: 'DOM fixture; actual catalogue, fixture image bytes, no full town', runs: [] };
const out = process.env.HUNT_TEST_OUT;
if (out) fs.mkdirSync(out, { recursive: true });
const imageBytes = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aR90AAAAASUVORK5CYII=', 'base64');
try {
  for (const width of [390, 1280]) {
    const context = await browser.newContext({ viewport: { width, height: width === 390 ? 780 : 800 } });
    const page = await context.newPage(); const errors = []; const requests = []; let failImage = false;
    const run = { width, checks: [], errors }; report.runs.push(run);
    page.on('pageerror', error => errors.push(error.message));
    await page.route('https://kevinrhaas.github.io/chicago-images/**', route => {
      requests.push(route.request().url());
      return route.fulfill({ status: failImage ? 503 : 200, contentType: failImage ? 'text/plain' : 'image/png',
        body: failImage ? Buffer.from('Photograph unavailable') : imageBytes });
    });
    const day = '2026-11-18', order = huntOrder(day);
    await page.goto(`${origin}/1904/?year=1904&nav=home&hunt=1&huntDay=${day}`);
    await page.getByRole('button', { name: 'Open five-photo hunt', exact: true }).waitFor();
    assert.equal(await page.evaluate(() => fixture.loads), 0); assert.equal(requests.length, 0);
    await page.getByRole('button', { name: 'Open five-photo hunt', exact: true }).focus();
    await page.keyboard.press('Enter');
    await page.getByRole('button', { name: 'Guess this spot', exact: true }).waitFor();
    await page.waitForFunction(() => !document.querySelector('.photo-hunt button')?.disabled && document.querySelector('.photo-hunt-image')?.complete);
    assert.equal(requests.length, 1, 'only one photo is requested');
    assert(requests[0].endsWith(`${order[0]}-thumb.jpg`));
    assert.equal(await page.locator('.photo-hunt-image[src]').count(), 1);
    await page.evaluate(async () => {
      await fixture.rail.select('other'); fixture.level = 0; fixture.rail.setVisible(false);
    });
    assert.equal(await page.locator('.photo-hunt-image[src]').count(), 0);
    const beforeQuiet = requests.length;
    await page.evaluate(async () => {
      await fixture.rail.select('home', { by: 'quiet' });
      fixture.rail.setVisible(false); // Already docked: the registry deliberately does not call hidden again.
    });
    assert.equal(await page.evaluate(() => fixture.rail.current), 'home');
    assert.equal(await page.locator('.photo-hunt-image[src]').count(), 0, 'quiet Home selection while docked must not restore the image');
    assert.equal(requests.length, beforeQuiet, 'quiet docked Home requests no photograph');
    await page.evaluate(() => { fixture.level = 1; fixture.rail.setVisible(true); });
    await page.waitForFunction(() => document.querySelector('.photo-hunt-image[src]')?.complete);
    assert.equal(await page.locator('.photo-hunt-image[src]').count(), 1, 'opening the Navigator restores its one current image');
    await page.evaluate(() => fixture.home.shown(document.getElementById('nav-home'), { ...fixture.context, navigator: undefined }));
    assert.equal(await page.locator('.photo-hunt-image[src]').count(), 1, 'standalone Home contexts without a Navigator remain visible');
    run.checks.push('actual nav-rail other app → dock → quiet Home keeps image released until reopening; standalone context remains supported');
    assert.equal(await page.getByRole('button', { name: 'Visit the camera spot', exact: true }).count(), 0);
    assert.equal(await page.getByRole('link', { name: 'Read the source', exact: true }).count(), 0);
    await page.getByRole('button', { name: 'Guess this spot', exact: true }).focus();
    await page.keyboard.press('Space');
    await page.getByText('Enter the town before making a guess.', { exact: true }).waitFor();
    await page.evaluate(id => { const row = fixture.destinations.byId('photo', id); fixture.pose = { e: row.e + 100, n: row.n }; }, order[0]);
    await page.getByRole('button', { name: 'Guess this spot', exact: true }).click();
    await page.getByText('100 metres from the camera spot · 150 points', { exact: true }).waitFor();
    assert.equal(await page.evaluate(() => document.activeElement.textContent), 'Photograph 1 of 5', 'reveal focus remains in the hunt');
    assert.equal(await page.getByRole('button', { name: 'Guess this spot', exact: true }).count(), 0);
    assert.equal(await page.getByRole('link', { name: 'Read the source', exact: true }).count(), 1);
    assert.match(await page.locator('.photo-hunt-content').innerText(), /Recorded year range:.*Source’s date description:/s);
    await page.evaluate(() => { fixture.blocked = true; });
    await page.getByRole('button', { name: 'Visit the camera spot', exact: true }).click();
    await page.getByText('The recorded camera spot cannot be safely visited right now.', { exact: true }).waitFor();
    await page.evaluate(() => { fixture.blocked = false; });
    await page.getByRole('button', { name: 'Visit the camera spot', exact: true }).click();
    assert.deepEqual(await page.evaluate(() => fixture.visits), [order[0]]);
    run.checks.push('lazy single image, no pre-guess reveal/travel, live position, distance score, guarded visit, real source dates');
    console.log(`${width}: initial photo, score and source reveal pass`);
    await page.getByRole('button', { name: 'Next photograph', exact: true }).click();
    await page.getByRole('button', { name: 'Skip and reveal', exact: true }).click();
    await page.getByRole('button', { name: 'Next photograph', exact: true }).click();
    await page.reload();
    await page.getByRole('button', { name: 'Open five-photo hunt', exact: true }).click();
    await page.getByRole('heading', { name: 'Photograph 3 of 5', exact: true }).waitFor();
    assert.equal(await page.locator('.photo-hunt-image').getAttribute('src'), `https://kevinrhaas.github.io/chicago-images/prairie-1904/files/${order[2]}-thumb.jpg`);
    await page.getByRole('button', { name: 'Return to the town', exact: true }).click();
    assert.equal(await page.locator('.photo-hunt-image[src]').count(), 0, 'hidden Home releases the image');
    await page.evaluate(() => { fixture.level = 1; fixture.rail.setVisible(true); });
    await page.waitForFunction(() => [...document.querySelectorAll('.photo-hunt button')].some(b => b.textContent === 'Guess this spot' && !b.disabled));
    await page.evaluate(id => { const row = fixture.destinations.byId('photo', id); fixture.pose = { e: row.e, n: row.n }; }, order[2]);
    await page.getByRole('button', { name: 'Guess this spot', exact: true }).click();
    // Fail a photograph this document has not decoded, rather than an image Chromium
    // can legitimately restore from its decoded cache after Home hides and shows it.
    failImage = true;
    await page.getByRole('button', { name: 'Next photograph', exact: true }).click();
    await page.getByRole('button', { name: 'Try loading this photo again', exact: true }).waitFor({ state: 'visible' });
    assert(await page.getByRole('button', { name: 'Guess this spot', exact: true }).isDisabled());
    failImage = false;
    await page.getByRole('button', { name: 'Try loading this photo again', exact: true }).click();
    await page.waitForFunction(() => [...document.querySelectorAll('.photo-hunt button')].some(b => b.textContent === 'Guess this spot' && !b.disabled));
    for (let i = 3; i < 5; i++) {
      await page.waitForFunction(() => [...document.querySelectorAll('.photo-hunt button')].some(b => b.textContent === 'Guess this spot' && !b.disabled));
      await page.evaluate(id => { const row = fixture.destinations.byId('photo', id); fixture.pose = { e: row.e, n: row.n }; }, order[i]);
      await page.getByRole('button', { name: 'Guess this spot', exact: true }).click();
      await page.getByRole('button', { name: i === 4 ? 'Finish hunt' : 'Next photograph', exact: true }).click();
    }
    await page.getByRole('heading', { name: 'Five-photo hunt complete', exact: true }).waitFor();
    assert.equal(await page.locator('.photo-hunt-image[src]').count(), 0);
    await page.getByText('3150 of 5,000 points', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Copy challenge link', exact: true }).click();
    const shared = new URL(await page.getByRole('textbox', { name: 'Challenge link', exact: true }).inputValue());
    assert.equal(shared.searchParams.get('huntDay'), day);
    assert.deepEqual([...shared.searchParams.keys()], ['year', 'nav', 'hunt', 'huntDay']);
    assert.equal(await page.evaluate(() => document.activeElement.getAttribute('aria-label')), 'Challenge link');
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    run.checks.push('reload preserves round order and score, hidden image cleanup, image failure/retry, five-photo completion, clipboard fallback, no overflow');
    console.log(`${width}: persistence, image failure/retry and completion pass`);
    if (out) await page.screenshot({ path: path.join(out, `${width}-complete.png`) });
    await page.evaluate(key => localStorage.setItem(key, '{broken'), HUNT_STORAGE_KEY);
    await page.reload(); await page.getByRole('button', { name: 'Open five-photo hunt', exact: true }).click();
    await page.getByText('Saved progress could not be read. Play here, or start again to replace the saved record.', { exact: true }).waitFor();
    assert.equal(await page.evaluate(key => localStorage.getItem(key), HUNT_STORAGE_KEY), '{broken');
    await page.getByRole('button', { name: 'Start this hunt again', exact: true }).click();
    await page.getByText('Progress saved in this browser.', { exact: true }).waitFor();
    await page.evaluate(() => { Storage.prototype.setItem = () => { throw new Error('blocked'); }; });
    await page.getByRole('button', { name: 'Skip and reveal', exact: true }).click();
    await page.getByText('Progress could not be saved. You can keep playing in this tab.', { exact: true }).waitFor();
    assert.equal(await page.getByRole('button', { name: 'Next photograph', exact: true }).count(), 1);
    run.checks.push('visible corrupt/blocked storage handling; in-memory play remains possible');
    console.log(`${width}: corrupt/blocked storage and cleanup pass`);
    await page.evaluate(() => { fixture.home.unmount(document.getElementById('nav-home')); });
    assert.equal(await page.locator('#nav-photo-hunt').count(), 0);
    assert.deepEqual(errors, []);
    await context.close();
  }
  console.log('PHOTO HUNT VIEW PASS — complete mobile/desktop keyboard-labelled Home flow, deterministic saved links, one image, reveal/travel, failures and storage errors');
} finally {
  if (out) fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2));
  await browser.close(); server.close();
}
