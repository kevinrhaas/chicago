// T-3534: actual-town DATA/AUDIO qualification, with an explicit source overlay on a
// generated publication snapshot. This is NOT pixel/render or regenerated-site
// acceptance. Real fauna, flora geometry, terrain, date/hour/season and R2 bytes
// are retained. Only the non-pixel reads hold draws (camera matrices still update).
// C4D_SOURCE_ROOT=... C4D_PUBLISHED_ROOT=... NODE_PATH=... node tools/test_habitat_audio_town.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = process.env.C4D_SOURCE_ROOT ?? root;
const published = process.env.C4D_PUBLISHED_ROOT;
assert(published, 'Set C4D_PUBLISHED_ROOT to an immutable generated publication snapshot');
const policy = JSON.parse(await fs.readFile(path.join(source, 'tools/audio-hosting.json'), 'utf8'));
const catalog = JSON.parse(await fs.readFile(path.join(root, 'renderers/web/audio/catalog.json'), 'utf8'));
for (const a of catalog.assets) for (const key of a.kind === 'music' ? ['opus', 'aac'] : ['url']) {
 const hash = a.kind === 'music' ? a.delivery[key].sha256 : a.delivery.sha256;
 a[key] = new URL(`media/${hash}${path.extname(a[key])}`, policy.public_base).href;
}
const overlayNames = ['main.js', 'fauna.js', 'recorded-audio.js', 'habitat-audio.js'];
const overlays = new Map(await Promise.all(overlayNames.map(async name =>
 ['/walk/js/' + name, await fs.readFile(path.join(root, 'renderers/web/js', name))])));
overlays.set('/walk/audio/catalog.json', Buffer.from(JSON.stringify(catalog)));
const mime = { '.js': 'text/javascript', '.json': 'application/json', '.html': 'text/html', '.css': 'text/css', '.wasm': 'application/wasm', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.glb': 'model/gltf-binary' };
let pw; try { pw = await import('playwright'); }
catch { pw = await import(path.join(process.env.NODE_PATH, 'playwright/index.mjs')); }
const widths = process.env.HABITAT_VIEWPORT ? [Number(process.env.HABITAT_VIEWPORT)] : [390, 1280];
console.log('Qualification: actual-town data/audio, SOURCE OVERLAY on ' + published + '; no pixel or regenerated-publication claim');
for (const width of widths) {
 const browser = await pw.chromium.launch({ executablePath: process.env.PW_EXECUTABLE ?? '/usr/bin/chromium', headless: true, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
 const context = await browser.newContext({ viewport: { width, height: width === 390 ? 780 : 800 }, hasTouch: width === 390, deviceScaleFactor: width === 390 ? 2 : 1, serviceWorkers: 'block' });
 const page = await context.newPage(), errors = [], requests = [], responses = [], notFound = [];
 page.setDefaultTimeout(90000);
 page.on('pageerror', e => errors.push(e.message));
 page.on('request', r => { if (r.url().startsWith(policy.public_base)) requests.push(r.url()); });
 page.on('response', r => { if (r.url().startsWith(policy.public_base)) responses.push({ url: r.url(), status: r.status() }); });
 await context.route(policy.origin + '/**', async route => {
  const u = new URL(route.request().url());
  const relative = decodeURIComponent(u.pathname).replace(/^\/4d(?=\/)/, '');
  if (overlays.has(relative)) return route.fulfill({ body: overlays.get(relative), contentType: mime[path.extname(relative)] });
  let file = path.resolve(published, '.' + relative);
  if (!file.startsWith(path.resolve(published) + path.sep)) return route.fulfill({ status: 403 });
  try {
   if ((await fs.stat(file)).isDirectory()) file = path.join(file, 'index.html');
   return route.fulfill({ body: await fs.readFile(file), contentType: mime[path.extname(file)] ?? 'application/octet-stream' });
  } catch { notFound.push(relative); return route.fulfill({ status: 404, body: relative }); }
 });
 await page.addInitScript(() => localStorage.setItem('chicago4d.settings', JSON.stringify({ soundMaster: 0, soundAmbience: 1, soundMusic: 0, timeOfDay: '15:00' })));
 let held = false;
 const holdDraws = async on => {
  await page.evaluate(hold => {
   const r = window.__chicago4d.renderer;
   if (hold && !window.__habitatHeldDraw) {
    window.__habitatHeldDraw = r.render;
    r.render = (scene, camera) => { camera?.updateMatrixWorld?.(); };
   } else if (!hold && window.__habitatHeldDraw) {
    r.render = window.__habitatHeldDraw; delete window.__habitatHeldDraw;
   }
  }, on); held = on;
 };
 try {
  const start = Date.now();
  await page.goto(policy.origin + '/4d/walk/?year=1835&keep-geometry=1', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240000, polling: 1000 });
  console.log(`${width}px: actual town ready in ${((Date.now() - start)/1000).toFixed(1)}s`);
  await holdDraws(true);
  assert.equal(requests.length, 0, 'muted boot requests no audio');
  const stations = await page.evaluate(async () => {
   const a = window.__chicago4d;
   const h = await import('./js/habitat-audio.js');
   const c = await (await fetch('./audio/catalog.json')).json();
   window.__ha = { ...h, catalog: c, clock: 0 };
   await a.timeOfDay.set('15:00', { date: '1835-07-01' });
   const found = {};
   for (let e = -900; e <= 1500; e += 12) for (let n = -900; n <= 1100; n += 12) {
    if (!a.terrain.heightfield.contains(e, n)) continue;
    const z = a.flora.zoneAt(e, n);
    if (!['z01_wet_prairie', 'z04_marsh'].includes(z) || found[z]) continue;
    const ground = a.terrain.surfaceHeight(e, n); if (!Number.isFinite(ground)) continue;
    const y = Math.max(0, ground);
    const camera = a.camera.clone(); camera.position.set(e, y + 1.7, -n); camera.quaternion.set(0,0,0,1);
    const env = { camera, terrain: a.terrain, flora: a.flora, faunaZones: a.fauna.records, season: a.season.current, time: a.timeOfDay.current, sunElevation: a.world.sun.elevationDeg };
    const candidates = h.habitatCandidates(c, env, '1835');
    const expected = z === 'z01_wet_prairie' ? 'summer-cicada-proxy' : 'redwing-call';
    if (!candidates.some(x => x.asset.id === expected)) continue;
    found[z] = { e, n, y, candidate: candidates.find(x => x.asset.id === expected) };
   }
   __ha.stations = found;
   __ha.environment = () => ({ camera: __ha.camera ?? a.camera, terrain: a.terrain, flora: a.flora, faunaZones: a.fauna.records,
    season: a.season.current, time: a.timeOfDay.current, sunElevation: a.world.sun.elevationDeg });
   __ha.candidates = () => __ha.habitatCandidates(__ha.catalog, __ha.environment(), '1835');
   const p = found.z01_wet_prairie;
   if (p) { a.walker.teleport({ local_e: p.e, local_n: p.n, yaw_deg: 0 }); a.step(); a.step(); }
   return { found, fauna: a.fauna.records.length, time: a.timeOfDay.current, season: a.season.current };
  });
  assert.equal(stations.fauna, 10);
  assert(stations.found.z01_wet_prairie && stations.found.z04_marsh, 'real ground supports both prairie insects and distant marsh bird');
  console.log(`${width}px: real habitat stations ${JSON.stringify(stations.found, (k,v) => k === 'asset' || k === 'placement' ? undefined : v)}`);
  // The real speaker click owns autoplay; then the integrated mixer uses its own
  // real timer and the actual camera, fauna, flora, date/hour and ambient setting.
  await page.click('#arrival-sound');
  await page.evaluate(async () => {
   const a = __chicago4d, welcome = a.welcome;
   if(welcome) {
    const deadline = Date.now()+90000;
    while(welcome.state !== 'world' && Date.now()<deadline) {
     if(welcome.state === 'welcome') welcome.enter('spawn');
     if(welcome.state !== 'world') await new Promise(resolve=>setTimeout(resolve,100));
    }
    if(welcome.state !== 'world') throw Error('actual town entry did not complete');
   }
   // Arrival settling/entry can restore spawn; place the listener only after it.
   const p = __ha.stations.z01_wet_prairie;
   a.walker.teleport({local_e:p.e,local_n:p.n,yaw_deg:0}); a.step(); a.step();
   document.exitPointerLock?.();
  });
  await page.waitForFunction(() => __chicago4d.sound?.state.recorded?.habitat?.voices.includes('summer-cicada-proxy'), null, { timeout: 35000, polling: 100 });
  assert(await page.evaluate(() => __chicago4d.sound.state.recorded.decodedBytes <= 14*1024*1024 + 24*48000*4));
  await page.evaluate(() => {
   const a = __chicago4d;
   a.hud.settings.soundAmbience = 0; a.sound.sync();
  });
  assert(await page.evaluate(() => __chicago4d.sound.state.recorded.habitat.voices.length === 0 && __chicago4d.sound.state.recorded.habitat.decodedBytes === 0));
  console.log(`${width}px: real integrated mixer schedules prairie cicada and ambience mute clears its voice/cache`);
  // Deterministic scheduling clock only; actual Web Audio, R2 recording and live
  // scene environment remain real. Controlled listener poses allow fixed-anchor
  // checks without asking the walker to move across marsh water in real time.
  await page.evaluate(() => {
   const a = __chicago4d, h = __ha;
   h.camera = a.camera.clone();
   h.output = a.audio.createGain(); h.output.gain.value = .5;
   h.meter = a.audio.createAnalyser(); h.output.connect(h.meter); h.meter.connect(a.audio.destination);
   h.engine = h.createHabitatAudio({ ctx: a.audio, output: h.output, catalog: () => h.catalog,
    environment: h.environment, now: () => h.clock, random: () => .5 });
   h.sync = () => h.engine.sync({ enabled: true, year: '1835' });
   h.start = station => {
    h.engine.reset(); const s = h.stations[station];
    h.camera.position.set(s.e, s.y + 1.7, -s.n); h.camera.quaternion.set(0,0,0,1);
    h.clock += 50000; h.sync(); h.clock += 30000; h.sync();
   };
   h.peak = () => { const f = new Float32Array(h.meter.fftSize); h.meter.getFloatTimeDomainData(f); return Math.max(...f.map(Math.abs)); };
  });
  await page.evaluate(async () => { await __chicago4d.timeOfDay.set('22:00'); __ha.start('z01_wet_prairie'); });
  await page.waitForFunction(() => __ha.engine.state.voices.includes('summer-crickets') && __ha.peak() > .000001, null, { timeout: 30000, polling: 50 });
  const night = await page.evaluate(() => ({ period: __ha.habitatPeriod(__ha.environment()), ids: __ha.candidates().map(c => c.asset.id) }));
  assert.equal(night.period, 'night'); assert(night.ids.includes('summer-crickets')); assert(!night.ids.includes('summer-cicada-proxy')); assert(!night.ids.includes('redwing-call'));
  await page.evaluate(async () => { await __chicago4d.timeOfDay.set('09:00'); __ha.sync(); });
  await page.waitForFunction(() => !__ha.engine.state.voices.length, null, { timeout: 1000, polling: 50 });
  assert(!(await page.evaluate(() => __ha.candidates().map(c => c.asset.id))).includes('summer-cicada-proxy'), 'actual morning suppresses cicada');
  await page.evaluate(async () => { await __chicago4d.timeOfDay.set('15:00'); __ha.start('z04_marsh'); });
  await page.waitForFunction(() => __ha.engine.state.voices.includes('redwing-call') && __ha.peak() > .000001, null, { timeout: 30000, polling: 50 });
  const bird = await page.evaluate(() => {
   const h = __ha, p = h.camera.position, anchor = h.engine.state.anchor;
   const distance = Math.hypot(anchor.x-p.x, anchor.y-p.y, anchor.z-p.z);
   const zone = __chicago4d.flora.zoneAt(anchor.x, -anchor.z);
   const before = {...anchor}; h.camera.position.x += 1; h.sync();
   return {distance, zone, before, after: h.engine.state.anchor, zBehind: anchor.z > p.z};
  });
  assert(bird.distance >= 36 && bird.distance < 96 && bird.zBehind);
  assert(['z03_sedge_meadow','z04_marsh'].includes(bird.zone)); assert.deepEqual(bird.before,bird.after);
  await page.evaluate(() => { const h=__ha,a=h.engine.state.anchor; h.camera.position.set(a.x,a.y,a.z-10); h.sync(); });
  await page.waitForFunction(() => !__ha.engine.state.voices.length, null, { timeout: 1000, polling: 50 });
  for (const reason of ['far','in-view']) {
   await page.evaluate(() => __ha.start('z04_marsh'));
   await page.waitForFunction(() => __ha.engine.state.voices.includes('redwing-call'), null, { timeout: 30000, polling: 50 });
   await page.evaluate(reason => {
    const h=__ha,a=h.engine.state.anchor;
    if(reason==='far') h.camera.position.set(a.x,a.y,a.z-120);
    else h.camera.lookAt(a.x,a.y,a.z);
    h.sync();
   }, reason);
   await page.waitForFunction(() => !__ha.engine.state.voices.length, null, { timeout: 1000, polling: 50 });
  }
  // Change the real solar date, then real season API. No date/season stubs.
  await page.evaluate(async () => { await __chicago4d.timeOfDay.set('15:00',{date:'1835-07-02'}); __ha.start('z01_wet_prairie'); });
  assert(await page.evaluate(() => __ha.candidates().length === 0 && !__ha.engine.state.active && __ha.engine.state.decodedBytes === 0));
  await page.evaluate(async () => { await __chicago4d.timeOfDay.set('15:00',{date:'1835-07-01'}); await __chicago4d.season.set('winter'); __ha.sync(); });
  assert(await page.evaluate(() => __chicago4d.season.current === 'winter' && !__ha.engine.state.active && !__ha.candidates().length));
  const water = await page.evaluate(async () => {
   const t = __chicago4d.terrain, z = __ha.catalog.water_zones['1835'];
   const {nearbyWater, waterKind} = await import('./js/recorded-audio.js');
   const samples = {}, tested = new Set();
   const inspect = (e,n) => {
    const key = `${e},${n}`; if(tested.has(key)) return; tested.add(key);
    if(!t.heightfield.contains(e,n) || !t.isWater(e,n)) return;
    const wet = nearbyWater(t,{x:e,y:1.7,z:-n}), kind=waterKind(wet,t,z);
    if(kind && !samples[kind]) samples[kind]={e,n,wet,ground:t.surfaceHeight(e,n),walkBarrier:t.height(e,n)};
   };
   // Authored slough line points first, accepting only actually wet heightfield
   // locations. A drawn hydrology line alone is not evidence of wet terrain.
   for(const f of z.features.filter(f=>f.kind==='slough')) for(let i=1;i<f.line.length;i++) {
    const a=f.line[i-1],b=f.line[i];
    for(const fraction of [0,.25,.5,.75,1]) inspect(a[0]+fraction*(b[0]-a[0]),a[1]+fraction*(b[1]-a[1]));
   }
   for(let e=-900;e<=1900 && (!samples.river || !samples.lake);e+=40)
    for(let n=-900;n<=1100 && (!samples.river || !samples.lake);n+=40) inspect(e,n);
   return {loaded:t.loaded,epoch:t.epochId,catalogueEpoch:z.epoch,
    shore:t.lakeShore?{n0:t.lakeShore.n0,step:t.lakeShore.step,samples:t.lakeShore.e.length}:null,
    samples,notSampled:['river','lake','slough'].filter(k=>!samples[k])};
  });
  assert(water.loaded && water.epoch === water.catalogueEpoch);
  console.log(`${width}px: actual water classifications only (not audibility or pixel evidence): ${JSON.stringify(water)}`);
  assert(await page.evaluate(() => __ha.engine.state.errors.length === 0));
  assert.deepEqual(errors, []); assert(responses.every(r => r.status >= 200 && r.status < 300), JSON.stringify(responses));
  const live = catalog.assets.filter(a => a.runtime_enabled && ['habitat-insects', 'distant-bird'].includes(a.scene_placement?.mode)).map(a => a.url);
  for (const url of live) assert(requests.includes(url), `actual R2 request: ${url}`);
  console.log(`HABITAT TOWN OVERLAY PASS ${width}px: real prairie/marsh, real scene hour/date/season, integrated ambience lifecycle, real cricket/bird samples, fixed distant rear anchor, near/far/in-view silence; zero page errors. No pixel qualification.`);
 } catch (error) {
  console.error(JSON.stringify({ width, pageErrors: errors, notFound, diagnostic: await page.evaluate(() => ({ ready: window.__chicago4d?.ready, error: window.__chicago4d?.error, gate: document.getElementById('gate')?.innerText?.slice(0, 1600) })).catch(() => null) }));
  throw error;
 } finally {
  if (!page.isClosed()) {
   await page.evaluate(() => { window.__ha?.engine?.dispose(); window.__ha?.output?.disconnect(); window.__ha?.meter?.disconnect(); window.__chicago4d?.sound?.dispose(); }).catch(() => {});
   if (held) await holdDraws(false).catch(() => {});
  }
  await browser.close();
 }
}
