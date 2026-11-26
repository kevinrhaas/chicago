/** Real Home and hunt modules, real compiled catalogue, small image fixtures; no 3D world. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { huntOrder, huntSet, huntCount, HUNT_STORAGE_KEY } from '../renderers/web/js/photo-hunt.js';

const { chromium } = createRequire(import.meta.url)('playwright');
const root = path.resolve(new URL('..', import.meta.url).pathname);
const web = path.join(root, 'renderers/web');
assert(!/<link[^>]+href=["'][^"']*\/photo-hunt\.css["']/.test(fs.readFileSync(path.join(web, 'index.html'), 'utf8')),
  'photo-hunt.css must not load globally before its panel is mounted');
const docs = JSON.parse(execFileSync('python3', ['-c',
  'import sys,json;sys.path.insert(0,"tools");import compile_pictures as p;print(json.dumps(p.add_place_names(p.derive(*p.read_tree()),p.load_json(p.PLACE_NAMES))))'], { cwd: root, maxBuffer: 64 * 1024 * 1024 }));
// One fixture per scene with a hunt (T-3677), each the real catalogue of its own year.
const fixtures = {};
for (const year of ['1904', '1812', '1835', '1871']) { // every year has a set since T-3764
  const doc = docs[year], registry = [];
  for (const id of Object.keys(doc.by_structure)) {
    const file = path.join(root, 'data/sidecars', year, `${id}.json`);
    if (fs.existsSync(file)) registry.push([id, { sidecar: JSON.parse(fs.readFileSync(file)) }]);
  }
  fixtures[year] = JSON.stringify({ doc, registry });
}
const pageHTML = `<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root { --ink: #ecf0f3; --panel-raised: #252e38; --edge: #8994a1; color:var(--ink); background:#18212a; font:16px system-ui; }
body { margin:0; } #nav-home { max-width:400px; box-sizing:border-box; padding:8px; } a { color:#97d6ff; }</style></head>
<body><nav id="fixture-rail" aria-label="Navigator apps"></nav><div id="fixture-screens"><div id="nav-home"></div></div><script type="module">
import home from '/js/apps/home.js';
import { createDestinations } from '/js/destinations.js';
import { createRail } from '/js/nav-rail.js';
window.fixture = { loads:0, visits:[], blocked:false, pose:null, home, level:1 };
const sceneYear = location.pathname.split('/')[1] || '1904';
const context = { scene:{id:sceneYear}, api:{}, navigator:{get level(){return fixture.level;}}, actions:{
 freeRoam:()=>{fixture.level=0; fixture.rail.setVisible(false); fixture.roamed=true;},
 photoHunt:{
  async load(){ fixture.loads++; const data=await fetch('/fixture-'+sceneYear+'.json').then(r=>r.json());
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
  if (pathname === '/' || /^\/(1904|1812|1835|1871|1600)\/$/.test(pathname)) { res.setHeader('Content-Type', 'text/html'); res.end(pageHTML); return; }
  const fx = /^\/fixture-(\d{4})\.json$/.exec(pathname);
  if (fx && fixtures[fx[1]]) { res.setHeader('Content-Type', 'application/json'); res.end(fixtures[fx[1]]); return; }
  const file = path.resolve(web, `.${pathname}`);
  if (!file.startsWith(`${web}/`)) { res.writeHead(403); res.end(); return; }
  fs.readFile(file, (error, bytes) => { res.writeHead(error ? 404 : 200, { 'Content-Type': file.endsWith('.js') ? 'text/javascript'
    : file.endsWith('.css') ? 'text/css' : 'application/octet-stream' }); res.end(error ? '' : bytes); });
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || '/usr/bin/chromium', args: ['--no-sandbox'] });
const report = { kind: 'DOM fixture; actual catalogue, fixture image bytes, no full town', runs: [] };
const out = process.env.HUNT_TEST_OUT;
if (out) fs.mkdirSync(out, { recursive: true });
const imageBytes = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aR90AAAAASUVORK5CYII=', 'base64');
async function loadedReveal(page) {
  await page.locator('.photo-hunt-image').evaluate(image => image.decode());
  const status = page.getByText('Photograph loaded.', { exact: true }); await status.waitFor();
  assert.equal(await status.getAttribute('role'), 'status'); assert.equal(await status.getAttribute('aria-live'), 'polite');
  assert.equal(await page.getByText('Loading this photograph…', { exact: true }).count(), 0);
  assert.equal(await page.getByRole('button', { name: 'Guess this spot', exact: true }).count(), 0, 'loaded reveal never invites another guess');
}
try {
  for (const width of [390, 1280]) {
    const context = await browser.newContext({ viewport: { width, height: width === 390 ? 780 : 800 } });
    const page = await context.newPage(); const errors = []; const requests = []; const styles = []; let failImage = false;
    const run = { width, checks: [], errors }; report.runs.push(run);
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => { if (new URL(request.url()).pathname === '/css/photo-hunt.css') styles.push(request.url()); });
    await page.route('https://kevinrhaas.github.io/chicago-images/**', route => {
      requests.push(route.request().url());
      return route.fulfill({ status: failImage ? 503 : 200, contentType: failImage ? 'text/plain' : 'image/png',
        body: failImage ? Buffer.from('Photograph unavailable') : imageBytes });
    });
    const day = '2026-11-18', order = huntOrder(day);
    await page.goto(`${origin}/1904/?year=1904&nav=home`);
    await page.locator('#nav-photo-hunt > summary').waitFor();
    assert.equal(await page.locator('link#photo-hunt-style').count(), 0);
    assert.deepEqual(styles, [], 'closed Home hunt requests no stylesheet');
    assert.equal(await page.evaluate(async () => {
      window.fixture.mountHunt = (await import('/js/photo-hunt-view.js')).mountPhotoHunt;
      return document.querySelectorAll('link#photo-hunt-style').length;
    }), 0, 'prefetching the module does not load CSS');
    assert.deepEqual(styles, []);
    await page.locator('#nav-photo-hunt > summary').click();
    await page.getByRole('button', { name: 'Open five-photo hunt', exact: true }).waitFor();
    await page.waitForFunction(() => getComputedStyle(document.querySelector('.photo-hunt-actions')).display === 'flex');
    assert.equal(await page.locator('link#photo-hunt-style').count(), 1);
    assert.equal(await page.getByRole('button', { name: 'Open five-photo hunt', exact: true }).evaluate(el => getComputedStyle(el).minHeight), '44px');
    assert.equal(styles.length, 1, 'first mount loads one stylesheet');
    assert.equal(await page.evaluate(() => {
      const host = document.createElement('div'); document.body.append(host);
      let mounted = fixture.mountHunt(host, { context: () => fixture.context });
      mounted.destroy(); mounted = fixture.mountHunt(host, { context: () => fixture.context }); mounted.destroy(); host.remove();
      return document.querySelectorAll('link#photo-hunt-style').length;
    }), 1, 'remounts reuse the document stylesheet');
    assert.equal(styles.length, 1);
    assert.deepEqual(await page.evaluate(async () => {
      const frame = document.createElement('iframe'); frame.id = 'hunt-style-frame';
      const loaded = new Promise(resolve => frame.addEventListener('load', resolve, { once: true }));
      frame.srcdoc = '<!doctype html><html><head></head><body><div id="hunt"></div></body></html>';
      document.body.append(frame); await loaded;
      const doc = frame.contentDocument, host = doc.getElementById('hunt');
      const before = doc.querySelectorAll('link[rel="stylesheet"]').length;
      let mounted = fixture.mountHunt(host, { context: () => fixture.context });
      mounted.destroy(); mounted = fixture.mountHunt(host, { context: () => fixture.context });
      return { before, count: doc.querySelectorAll('link#photo-hunt-style').length,
        owner: doc.getElementById('photo-hunt-style')?.ownerDocument === doc,
        path: new URL(doc.getElementById('photo-hunt-style').href).pathname };
    }), { before: 0, count: 1, owner: true, path: '/css/photo-hunt.css' });
    await page.waitForFunction(() => {
      const doc = document.getElementById('hunt-style-frame').contentDocument;
      return doc.defaultView.getComputedStyle(doc.querySelector('.photo-hunt-actions')).display === 'flex';
    });
    assert.equal(requests.length, 0, 'mounting styles alone loads no photograph');
    run.checks.push('CSS waits for mount, applies with text/css, deduplicates remounts, and belongs to each owner document');
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
    await loadedReveal(page);
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
    await page.reload(); await page.getByRole('button', { name: 'Open five-photo hunt', exact: true }).click();
    await page.getByRole('heading', { name: 'Photograph 1 of 5', exact: true }).waitFor();
    await loadedReveal(page);
    await page.getByText('100 metres from the camera spot · 150 points', { exact: true }).waitFor();
    failImage = true;
    await page.getByRole('button', { name: 'Next photograph', exact: true }).click();
    await page.getByRole('button', { name: 'Try loading this photo again', exact: true }).waitFor({ state: 'visible' });
    await page.getByRole('button', { name: 'Skip and reveal', exact: true }).click();
    await page.getByRole('button', { name: 'Try loading this photo again', exact: true }).waitFor({ state: 'visible' });
    assert.equal(await page.getByRole('button', { name: 'Guess this spot', exact: true }).count(), 0);
    failImage = false;
    await page.getByRole('button', { name: 'Try loading this photo again', exact: true }).click();
    await loadedReveal(page);
    await page.reload(); await page.getByRole('button', { name: 'Open five-photo hunt', exact: true }).click();
    await page.getByRole('heading', { name: 'Photograph 2 of 5', exact: true }).waitFor();
    await loadedReveal(page);
    await page.getByText('Skipped · 0 points', { exact: true }).waitFor();
    run.checks.push('guessed, skipped, retried and reloaded answered images announce loaded with polite status and no second guess');
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
  // T-3677: the 1835 set of prints and drawings; T-3764: 1812's (two found from a boat) and
  // 1871's photographs. A year with no set (a scene the fixture invents, 1600) says so.
  const kindText = { ENGRAVING: 'a print, an engraving', LITHO: 'a print, a lithograph', ILLUSTRATION: 'a drawing, printed in a book',
    PLATE: 'a printed plate', PHOTO: 'a photograph', STEREO: 'a photograph, one half of a stereograph card' };
  const words = {
    prints: (count, year) => ({ intro: `Find the spots that ${count} old prints and drawings of ${year} were drawn from.`,
      open: `Open the ${count}-picture hunt`, round: `Picture 1 of ${count}`, alt: /^Historical print or drawing for round 1\./,
      result: '50 metres from the spot it was drawn from · 407 points', visit: 'Visit the spot it was drawn from',
      next: 'Next picture', complete: `${count}-picture hunt complete` }),
    photos: (count, year) => ({ intro: `Find the camera spots of ${count} photographs of ${year} Chicago.`,
      open: `Open the ${count}-photo hunt`, round: `Photograph 1 of ${count}`, alt: /^Historical photograph for round 1\./,
      result: '50 metres from the camera spot · 407 points', visit: 'Visit the camera spot',
      next: 'Next photograph', complete: `${count}-photo hunt complete` }),
  };
  for (const width of [390, 1280]) {
    const context = await browser.newContext({ viewport: { width, height: width === 390 ? 780 : 800 } });
    const page = await context.newPage(); const errors = []; const requests = [];
    const run = { width, checks: [], errors }; report.runs.push(run);
    page.on('pageerror', error => errors.push(error.message));
    await page.route('https://kevinrhaas.github.io/chicago-images/**', route => {
      requests.push(route.request().url());
      return route.fulfill({ status: 200, contentType: 'image/png', body: imageBytes });
    });
    const day = '2026-11-18';
    await page.goto(`${origin}/1600/?year=1600&nav=home&hunt=1&huntDay=${day}`);
    await page.getByText('This year has no picture hunt yet: none of its pictures has a recorded camera spot. Choose another year in Other years to play.', { exact: true }).waitFor();
    assert.equal(await page.locator('.photo-hunt button').count(), 0, 'a year with no set offers no hunt to open');
    await page.goto(`${origin}/1904/?year=1835&nav=home&hunt=1&huntDay=2020-01-02`);
    await page.getByText('This challenge link is not valid. You can open today’s hunt instead.', { exact: true }).waitFor();
    assert.equal(await page.getByText('Challenge date: 2020-01-02 (UTC)', { exact: true }).count(), 0, 'a refused link does not set the day');
    run.checks.push('a year with no set says so; a link naming another year’s set is refused');
    for (const [year, kind] of [['1835', 'prints'], ['1812', 'prints'], ['1871', 'photos']]) {
      const count = huntCount(year), order = huntOrder(day, year), set = huntSet(year), w = words[kind](count, year);
      const fx = JSON.parse(fixtures[year]);
      requests.length = 0;
      await page.goto(`${origin}/${year}/?year=${year}&nav=home&hunt=1&huntDay=${day}`);
      await page.getByText(w.intro, { exact: true }).waitFor();
      await page.getByRole('button', { name: w.open, exact: true }).click();
      await page.getByRole('heading', { name: w.round, exact: true }).waitFor();
      await page.waitForFunction(() => [...document.querySelectorAll('.photo-hunt button')].some(b => b.textContent === 'Guess this spot' && !b.disabled));
      assert(requests[0].endsWith(`${order[0]}-thumb.jpg`)); assert.equal(requests.length, 1, 'one picture at a time');
      assert.match(await page.locator('.photo-hunt-image').getAttribute('alt'), w.alt);
      if (kind === 'prints') assert.doesNotMatch(await page.locator('.photo-hunt h3, .photo-hunt-content > p, .photo-hunt [role=status]').allInnerTexts().then(t => t.join(' ')),
        /photograph/i, 'a print or drawing is never called a photograph');
      let afloatSeen = 0;
      for (let i = 0; i < count; i++) {
        await page.waitForFunction(() => [...document.querySelectorAll('.photo-hunt button')].some(b => b.textContent === 'Guess this spot' && !b.disabled));
        const afloat = (set.afloat ?? []).includes(order[i]);
        assert.equal(await page.getByText('This view was drawn from the river. Take a boat out, and make your guess from the water.', { exact: true }).count(),
          afloat ? 1 : 0, `${order[i]}: the river hint shows only on a round drawn from the river`);
        await page.evaluate(id => { const row = fixture.destinations.byId('photo', id); fixture.pose = { e: row.e + 30, n: row.n + 40 }; }, order[i]);
        await page.getByRole('button', { name: 'Guess this spot', exact: true }).click();
        await page.getByText(w.result, { exact: true }).waitFor();
        const p = Object.values(fx.doc.by_structure).flat().find(p => p.id === order[i]);
        await page.getByText(`What it is: ${kindText[p.kind]}.`, { exact: true }).waitFor();
        const later = `Made in ${p.years[0]}, after this ${year} world. It shows the place as its maker pictured it.`;
        if (p.years[0] > Number(year)) await page.getByText(later, { exact: true }).waitFor();
        else assert.equal(await page.getByText(later, { exact: true }).count(), 0, `${order[i]}: made in its own year, never called later`);
        assert.match(await page.locator('.photo-hunt-content').innerText(), /Recorded year range:.*Source’s date description:/s);
        const tryVisit = i === 0 || (afloat && !afloatSeen);
        if (afloat) afloatSeen++;
        if (tryVisit) {
          const visits = await page.evaluate(() => fixture.visits.length);
          await page.getByRole('button', { name: w.visit, exact: true }).click();
          if (afloat) {
            await page.getByText('This spot is on the river: take a boat there.', { exact: true }).waitFor();
            assert.equal(await page.evaluate(() => fixture.visits.length), visits, 'a river spot is never walked to');
          } else assert.equal(await page.evaluate(() => fixture.visits.at(-1)), order[i]);
          if (out && i === 0) await page.screenshot({ path: path.join(out, `${width}-${year}-reveal.png`) });
        }
        await page.getByRole('button', { name: i === count - 1 ? 'Finish hunt' : w.next, exact: true }).click();
      }
      assert.equal(afloatSeen, (set.afloat ?? []).length, `${year}: every river round was played`);
      await page.getByRole('heading', { name: w.complete, exact: true }).waitFor();
      await page.getByText(`${count * 407} of ${(count * 1000).toLocaleString('en-US')} points`, { exact: true }).waitFor();
      const record = JSON.parse(await page.evaluate(key => localStorage.getItem(key), set.storageKey));
      assert.equal(record.year, year); assert.equal(record.cursor, count);
      assert.equal(await page.evaluate(key => localStorage.getItem(key), HUNT_STORAGE_KEY), null, `${year} never writes 1904’s progress`);
      await page.getByRole('button', { name: 'Copy challenge link', exact: true }).click();
      const shared = new URL(await page.getByRole('textbox', { name: 'Challenge link', exact: true }).inputValue());
      assert.equal(shared.searchParams.get('year'), year); assert.equal(shared.searchParams.get('huntDay'), day);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.reload(); await page.getByRole('button', { name: w.open, exact: true }).click();
      await page.getByRole('heading', { name: w.complete, exact: true }).waitFor();
      run.checks.push(`${year}: ${count} ${kind === 'prints' ? 'prints/drawings' : 'photographs'}, kind and date on each reveal, river rounds by boat, own storage and link, reload keeps the result`);
      console.log(`${width}: ${year} ${count}-${kind === 'prints' ? 'picture' : 'photo'} hunt passes`);
    }
    assert.deepEqual(errors, []);
    await context.close();
  }
  console.log('PHOTO HUNT VIEW PASS — complete mobile/desktop keyboard-labelled Home flow, deterministic saved links, one image, reveal/travel, failures and storage errors');
} finally {
  if (out) fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2));
  await browser.close(); server.close();
}
