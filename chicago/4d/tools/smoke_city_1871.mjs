#!/usr/bin/env node
/**
 * T-3654: exercise the published 1871 city, its real walker and its real renderer.
 *
 * node tools/smoke_city_1871.mjs --viewport mobile --out /tmp/city-1871-mobile
 * node tools/smoke_city_1871.mjs --viewport desktop --out /tmp/city-1871-desktop
 * node tools/smoke_city_1871.mjs --root /path/to/site/4d --viewport both
 * node tools/smoke_city_1871.mjs --viewport mobile --portal /tmp/1871-portal
 * node tools/smoke_city_1871.mjs --self-test
 *
 * Reads an already-published mirror; never publishes or changes data. Screenshots
 * and report.json go outside the repository by default. This is the additional
 * new-scene acceptance check, not a replacement for smoke_renderer's other years.
 * Driver draws/triangles are the app's measured frame counters. Visible buildings
 * are instances submitted by frustum-selected batches, not an occlusion census.
 * Heap bytes are measured by Chromium; GPU memory and hardware frame rate are not
 * inferred from them. Headless software-renderer timings are reported as such.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');

export function deckAxis(deck, beyond = 2) {
  const p = deck?.pts;
  if (!Array.isArray(p) || p.length !== 4 || !p.every(v => v.length === 2 && v.every(Number.isFinite))) {
    throw Error('A bridge acceptance reading needs four finite deck corners');
  }
  const length = i => Math.hypot(p[(i + 1) % 4][0] - p[i][0], p[(i + 1) % 4][1] - p[i][1]);
  const first = length(0) <= length(1) ? 0 : 1;
  const mid = i => p[i].map((v, k) => (v + p[(i + 1) % 4][k]) / 2);
  const a = mid(first), b = mid((first + 2) % 4);
  const span = Math.hypot(b[0] - a[0], b[1] - a[1]);
  if (!(span > 0) || !Number.isFinite(deck.y)) throw Error('Bridge has no finite walk-surface y or span');
  const unit = b.map((v, i) => (v - a[i]) / span);
  return { start: a.map((v, i) => v - unit[i] * beyond),
    end: b.map((v, i) => v + unit[i] * beyond), unit, length: span + 2 * beyond };
}

export function decodeBuildings(doc) {
  const fields = Object.fromEntries((doc.fields?.buildings ?? []).map((key, i) => [key, i]));
  return (doc.buildings ?? []).map(row => {
    const r = Array.isArray(row) ? Object.fromEntries(Object.entries(fields).map(([key, i]) => [key, row[i]])) : { ...row };
    for (const key of ['kit', 'district']) if (typeof r[key] === 'number') r[key] = doc.enums?.[key]?.[r[key]];
    return r;
  });
}

export function buildingClasses(rows) {
  return {
    commercial: rows.filter(r => /^(commercial_|frame_shop$)/.test(r.kit)),
    residential: rows.filter(r => /^(timber_|brick_|villa_)/.test(r.kit)),
    industrial: rows.filter(r => /^(warehouse|factory|industrial_shed)$/.test(r.kit)),
  };
}

export function selfTest() {
  assert.deepEqual(deckAxis({ pts: [[0, 0], [12, 0], [12, 80], [0, 80]], y: 3.34 }),
    { start: [6, -2], end: [6, 82], unit: [0, 1], length: 84 });
  const turned = deckAxis({ pts: [[0, 0], [80, 0], [80, 12], [0, 12]], y: 3.34 });
  assert.equal(turned.length, 84);
  assert.equal(turned.start[1], 6);
  assert.throws(() => deckAxis({ pts: [[0, 0], [12, 0], [12, 80], [0, 80]], height: 3.34 }), /walk-surface y/);
  const rows = decodeBuildings({ fields: { buildings: ['id', 'kit', 'district'] },
    enums: { kit: ['commercial_3', 'timber_house', 'factory'], district: ['centre'] },
    buildings: [['a', 0, 0], ['b', 1, 0], ['c', 2, 0]] });
  assert.equal(rows[0].district, 'centre');
  assert.deepEqual(Object.values(buildingClasses(rows)).map(r => r.length), [1, 1, 1]);
  console.log('CITY 1871 SELF-TEST PASS — rotated bridge traversal, y contract, packed placements and all district uses');
}

function parseArgs(args) {
  const opts = { root: path.resolve(ROOT, '../../site/4d'), viewport: 'both',
    out: path.join(os.tmpdir(), `chicago-1871-${Date.now()}`), tiers: ['light', 'balanced', 'full'] };
  for (let i = 0; i < args.length; i++) {
    const key = args[i];
    if (!['--root', '--viewport', '--out', '--tiers', '--portal'].includes(key) || !args[i + 1]) throw Error(`Unknown or incomplete option ${key}`);
    const value = args[++i];
    if (key === '--tiers') opts.tiers = value.split(',');
    else opts[key.slice(2)] = value;
  }
  if (!['mobile', 'desktop', 'both'].includes(opts.viewport)) throw Error('--viewport is mobile, desktop or both');
  if (!opts.tiers.length || opts.tiers.some(t => !['light', 'balanced', 'full'].includes(t))) throw Error('--tiers accepts light,balanced,full');
  opts.root = path.resolve(opts.root); opts.out = path.resolve(opts.out);
  return opts;
}

async function serverFor(root) {
  const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
    '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
    '.glb': 'model/gltf-binary', '.wasm': 'application/wasm', '.webmanifest': 'application/manifest+json' };
  const server = http.createServer((req, res) => {
    try {
      const url = new URL(req.url, 'http://local');
      let file = path.resolve(root, `.${decodeURIComponent(url.pathname)}`);
      if (file !== root && !file.startsWith(`${root}${path.sep}`)) throw Error('outside mirror');
      if (fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
      res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
      fs.createReadStream(file).pipe(res);
    } catch { res.writeHead(404); res.end('missing'); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  return server;
}

// Installed once in each page. Uses the actual app APIs; no replacement renderer.
function installReadings() {
  const api = () => window.__chicago4d;
  window.__city1871Read = {
    frame() {
      const a = api();
      a.step(); a.step();
      const gl = a.renderer.getContext(), pixels = new Uint8Array(gl.drawingBufferWidth * gl.drawingBufferHeight * 4);
      gl.readPixels(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
      return { pixels, stats: a.stats(), census: { ...a.contextCity.census } };
    },
    stand(spec, render = true) {
      const a = api();
      if (spec.anchor && a.goTo(spec.anchor)) { /* scene's own camera */ }
      else {
        const target = spec.target, eye = spec.eye;
        a.setFly(true);
        a.walker.teleport({ local_e: eye[0], local_n: eye[1], altitude_m: eye[2],
          yaw_deg: Math.atan2(target[0] - eye[0], target[1] - eye[1]) * 180 / Math.PI,
          pitch_deg: Math.atan2(target[2] - eye[2], Math.hypot(target[0] - eye[0], target[1] - eye[1])) * 180 / Math.PI });
      }
      if (!render) { a.contextCity.update(0, a.camera); return null; }
      return this.frame();
    },
    summarize(frame) {
      const p = frame.pixels;
      let nonBlack = 0, min = 255, max = 0;
      for (let i = 0; i < p.length; i += 4) {
        const v = (p[i] + p[i + 1] + p[i + 2]) / 3;
        if (v > 3) nonBlack++;
        min = Math.min(min, v); max = Math.max(max, v);
      }
      return { stats: frame.stats, census: frame.census, pixels: p.length / 4,
        camera: { e: api().camera.position.x, n: -api().camera.position.z, y: api().camera.position.y,
          altitude: api().walker.state.altitude },
        nonBlackShare: nonBlack / (p.length / 4), luminanceRange: max - min };
    },
    stepToward(target, steps, stepM = 0.16) {
      const a = api(), samples = [], dt = stepM / a.walkBudget.speed;
      const intent = { forward: 1, strafe: 0, sprint: false, flying: false,
        yawDelta: 0, pitchDelta: 0, clearLook() {} };
      for (let i = 0; i < steps; i++) {
        const s = a.walker.state;
        // Teleport sets the heading without bypassing walking for any step.
        const bearing = Math.atan2(target[0] - s.e, target[1] - s.n) * 180 / Math.PI;
        a.walker.teleport({ yaw_deg: bearing });
        a.walker.update(dt, intent);
        if (i % 10 === 0 || i === steps - 1) samples.push({ e: s.e, n: s.n, groundY: s.groundY, eyeY: s.eyeY, blocked: s.blocked });
      }
      return samples;
    },
  };
}

async function run(opts) {
  if (!fs.existsSync(path.join(opts.root, '1871/index.html'))) throw Error(`Publish first: ${opts.root}/1871/index.html does not exist`);
  const require = createRequire(import.meta.url);
  const { chromium } = require('playwright');
  fs.mkdirSync(opts.out, { recursive: true });
  const snapshotPaths = ['data/scenes/1871.json', 'data/context/1871.json', 'data/context/1871/kit.glb',
    'data/context/1871/kit.json', 'data/context/1871/generated-assets.json',
    'data/context/1871/streets.glb', 'data/context/1871/bridges.glb', 'data/context/1871/rail.glb',
    'data/terrain/epochs/e1871_prefire/heightfield.json', 'data/terrain/epochs/e1871_prefire/heightfield.bin',
    'walk/js/main.js', 'walk/js/city-context.js', 'walk/js/street-surfaces-1871.js', 'walk/js/walker.js',
    'walk/js/world.js', 'walk/js/time-of-day.js'];
  const snapshot = () => Object.fromEntries(snapshotPaths.map(rel => [rel,
    createHash('sha256').update(fs.readFileSync(path.join(opts.root, rel))).digest('hex')]));
  const report = { date: new Date().toISOString(), root: opts.root, viewport: opts.viewport, tiers: opts.tiers,
    completeDetailCoverage: ['light', 'balanced', 'full'].every(tier => opts.tiers.includes(tier)), snapshot: snapshot(),
    method: 'Published /1871/ actual app; own dated terrain; three detail tiers; real walker bridge traversal, quay access and building collision; same-frame confidence readback. Instances counted per selected batch, not occlusion-visible roofs. Driver GPU draws and submitted triangles; Chromium heap only, no GPU-memory or hardware-frame-time claim.',
    viewports: [], failures: [] };
  const check = (ok, text) => { if (!ok) { report.failures.push(text); console.error(`FAIL ${text}`); } else console.log(`PASS ${text}`); };
  const server = await serverFor(opts.root);
  const launch = { args: ['--no-sandbox', '--enable-unsafe-swiftshader'] };
  const executablePath = process.env.PW_EXECUTABLE || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  if (executablePath) launch.executablePath = executablePath;
  let browser;
  try { browser = await chromium.launch(launch); }
  catch (error) { await new Promise(resolve => server.close(resolve)); throw error; }
  try {
    for (const vp of [{ name: 'mobile', width: 390, height: 780 }, { name: 'desktop', width: 1280, height: 800 }]
      .filter(v => opts.viewport === 'both' || opts.viewport === v.name)) {
      const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 1,
        isMobile: vp.name === 'mobile', hasTouch: vp.name === 'mobile', reducedMotion: 'reduce' });
      const page = await ctx.newPage(); page.setDefaultTimeout(90_000);
      const row = { viewport: vp, errors: [], failedResponses: [], failedRequests: [], frames: [] };
      report.viewports.push(row);
      page.on('pageerror', error => row.errors.push(error.message));
      page.on('response', response => { if (response.status() >= 400) row.failedResponses.push({ url: response.url(), status: response.status() }); });
      page.on('requestfailed', request => row.failedRequests.push({ url: request.url(), error: request.failure()?.errorText }));
      try {
        const start = Date.now();
        await page.goto(`http://127.0.0.1:${server.address().port}/1871/?detail=light&seed=3654`, { waitUntil: 'domcontentloaded' });
        await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 240_000 });
        const bootError = await page.evaluate(() => window.__chicago4d?.error);
        if (bootError) throw Error(bootError);
        await page.waitForFunction(() => ['welcome', 'world'].includes(window.__chicago4d?.welcome?.state), null, { timeout: 90_000 });
        row.bootMs = Date.now() - start;
        await page.evaluate(() => {
          const a = window.__chicago4d;
          if (a.error) throw Error(a.error);
          if (a.welcome.state === 'welcome') a.welcome.enter('spawn');
          document.exitPointerLock?.(); document.getElementById('control-help-gotit')?.click();
          a.renderer.setAnimationLoop(null); a.setAnimationHold(true);
        });
        await page.waitForFunction(() => document.getElementById('gate')?.hidden === true, null, { timeout: 15_000 });
        await page.evaluate(installReadings);
        row.boot = await page.evaluate(() => {
          const a = window.__chicago4d, c = a.contextCity;
          return { scene: a.scene.id, date: a.scene.target_date, lighting: a.scene.lighting, epoch: a.scene.terrain_epoch, loadedEpoch: a.terrain.epochId,
            sunDate: a.world.sunDate, sunTime: a.world.sunTime, sun: a.world.describe(),
            seasonHidden: document.getElementById('row-season')?.hidden,
            sceneDayLabel: document.querySelector('#s-season option[value="summer"]')?.textContent,
            kind: c.doc?.kind, layers: a.sceneLayers, structures: [...a.registry].map(([id, r]) => ({ id, sidecar: r.sidecar })),
            census: c.census, doc: c.doc, problems: a.problems, streetLines: c.streetLines?.().length ?? 0,
            overflow: document.documentElement.scrollWidth > innerWidth };
        });
        const doc = row.boot.doc; delete row.boot.doc;
        const buildings = decodeBuildings(doc), uses = buildingClasses(buildings);
        check(row.boot.scene === '1871' && row.boot.date === '1871-10-08' && row.boot.lighting?.local_time === '16:00', `${vp.name}: date is the afternoon before the fire`);
        check(row.boot.sunDate === '1871-10-08' && row.boot.sunTime === '16:00', `${vp.name}: actual sun uses the scene's October afternoon`);
        check(row.boot.seasonHidden && /^Scene day/.test(row.boot.sceneDayLabel ?? '') && !/Summer/.test(row.boot.sceneDayLabel ?? ''),
          `${vp.name}: the dated autumn context does not offer an unsupported season change`);
        check(row.boot.epoch === 'e1871_prefire' && row.boot.loadedEpoch === 'e1871_prefire', `${vp.name}: dedicated pre-fire terrain loaded`);
        check(row.boot.kind === 'city_context_1871', `${vp.name}: 1871 context document loaded`);
        check(row.boot.structures.length === 0, `${vp.name}: context baseline imports no later named structures`);
        check(row.boot.layers.every(layer => !['humans', 'residents', 'street_grid'].includes(layer)), `${vp.name}: no other year's people or Prairie Avenue grid`);
        check(buildings.length >= 10_000 && row.boot.census.buildings === buildings.length - row.boot.census.dropped,
          `${vp.name}: entire-city building census reaches the renderer (${row.boot.census.buildings})`);
        check(Object.keys(row.boot.census.styleCounts).length >= 8 && Object.keys(row.boot.census.districtCounts).length >= 6,
          `${vp.name}: varied forms in multiple districts`);
        check(Object.values(uses).every(rows => rows.length > 0), `${vp.name}: commercial, residential and industrial forms present`);
        // T-3685: wood block, boulders, dirt and planks each painted, at the phone's smaller tile on light,
        // and the raised walks' kerb boards and crossing steps built from the floors.
        const surfacing = row.boot.census.streetSurfaces;
        check(surfacing?.dressed >= 4 && surfacing.edgeQuads > 10_000 && surfacing.tilePx === (surfacing.detail === 'light' ? 256 : 512),
          `${vp.name}: street surfaces painted (${surfacing?.dressed} materials, ${surfacing?.tilePx} px) with ${surfacing?.edgeQuads} kerb and step faces`);
        // Roadways, crossings and walks draw as ordered ground decals, so where two lie
        // one on the other (every junction and corner) they no longer blink (Kevin 2026-11-21).
        check(surfacing?.decals >= 3, `${vp.name}: street layers drawn as ordered decals (${surfacing?.decals} batches)`);
        const extents = buildings.reduce((b, r) => [Math.min(b[0], r.e), Math.max(b[1], r.e), Math.min(b[2], r.n), Math.max(b[3], r.n)], [Infinity, -Infinity, Infinity, -Infinity]);
        check(extents[1] - extents[0] > 5_000 && extents[3] - extents[2] > 7_000, `${vp.name}: city spans north, south and western districts`);
        check(row.boot.streetLines > 30 && (doc.walk_decks?.length ?? 0) > 0, `${vp.name}: dated streets and bridge decks available`);
        check(!row.boot.overflow, `${vp.name}: arrival fits viewport`);
        const candidates = Object.fromEntries(Object.entries(uses).map(([name, rows]) => [name,
          rows.toSorted((a, b) => Math.hypot(a.e, a.n) - Math.hypot(b.e, b.n)).slice(0, 24)]));
        // Find an actual clear street/yard view. A fixed eastward offset can put
        // the camera inside its neighbour and backlight every afternoon facade.
        const chosen = await page.evaluate(choices => {
          const a = window.__chicago4d, q = window.__city1871Read, result = [];
          for (const [name, rows] of Object.entries(choices)) {
            let found = null;
            for (const b of rows) {
              for (const [dx, dn] of [[-1, -.4], [-1, 0], [-1, .4], [0, -1], [0, 1], [1, 0]]) {
                const distance = Math.max(b.width_m, b.depth_m) * .7 + 12;
                const eye = [b.e + dx * distance, b.n + dn * distance, 2.1];
                if (a.contextCity.containsBuilding(eye[0], eye[1], 1) || a.terrain.isWater(eye[0], eye[1])) continue;
                const stand = { name, buildingId: b.id, eye, target: [b.e, b.n, b.eave_m * .45] };
                q.stand(stand, false);
                const hit = a.contextCity.pickAt(null, a.camera);
                if (hit?.id === `context:1871:${b.id}`) { found = { stand, subject: b }; break; }
              }
              if (found) break;
            }
            if (!found) throw Error(`No clear ground-level view of a ${name} building`);
            result.push(found);
          }
          return result;
        }, candidates);
        const subjects = Object.fromEntries(chosen.map(c => [c.stand.name, c.subject]));
        const stands = [{ name: 'whole-city', anchor: 'whole_city', eye: [3000, -3000, 900], target: [-1400, -1000, 0] },
          ...chosen.map(c => c.stand)];
        for (const tier of opts.tiers) {
          await page.evaluate(async level => { await window.__chicago4d.setDetail(level); }, tier);
          for (const stand of stands) {
            const reading = await page.evaluate(spec => {
              const q = window.__city1871Read;
              return { ...q.summarize(q.stand(spec)), detail: window.__chicago4d.detail };
            }, stand);
            row.frames.push({ tier, stand: stand.name, ...reading });
            check(reading.detail === tier && reading.census.visibleBuildings > 0, `${vp.name}/${tier}/${stand.name}: buildings render in this tier`);
            check(reading.stats.withinBudget, `${vp.name}/${tier}/${stand.name}: ${reading.stats.drawCalls} driver draws, ${reading.stats.triangles} triangles within declared budget`);
            check(reading.nonBlackShare > 0.3 && reading.luminanceRange > 20, `${vp.name}/${tier}/${stand.name}: nonblank scene pixels`);
            await page.screenshot({ path: path.join(opts.out, `${vp.name}-${tier}-${stand.name}.png`), timeout: 90_000 });
          }
        }
        // Same camera, same paused world: hide every reconstructed surface and restore it.
        row.confidence = await page.evaluate(stand => {
          const a = window.__chicago4d, q = window.__city1871Read;
          q.stand(stand); a.confidence.set(false); a.confidence.setHidden('reconstructed', false);
          const original = q.frame();
          a.confidence.setHidden('reconstructed', true); const hidden = q.frame();
          const hiddenPick = a.contextCity.pickAt(null, a.camera);
          a.confidence.setHidden('reconstructed', false); const restored = q.frame();
          const diff = (x, y) => { let changed = 0; for (let i = 0; i < x.length; i += 4) if (Math.max(...[0, 1, 2].map(k => Math.abs(x[i + k] - y[i + k]))) > 8) changed++; return changed; };
          let withoutChannel = 0, wrongGrade = 0;
          a.contextCity.group.traverse(o => { if (!o.isMesh) return; const attr = o.geometry.getAttribute('_confidence');
            if (!attr) withoutChannel++; else for (let i = 0; i < attr.count; i++) if (Math.abs(attr.getX(i) - 1) > 1e-6) { wrongGrade++; break; } });
          const hit = a.contextCity.pickAt(null, a.camera);
          a.contextCity.group.visible = false;
          const hiddenLayerPick = a.contextCity.pickAt(null, a.camera);
          a.contextCity.group.visible = true;
          return { pixels: original.pixels.length / 4, changed: diff(original.pixels, hidden.pixels), restoredChanged: diff(original.pixels, restored.pixels),
            withoutChannel, wrongGrade, hiddenPick: hiddenPick?.id ?? null, hiddenLayerPick: hiddenLayerPick?.id ?? null,
            pick: hit ? { id: hit.id, record: hit.record } : null };
        }, stands.find(s => s.name === 'commercial'));
        check(row.confidence.changed > row.confidence.pixels * .01 && row.confidence.restoredChanged < row.confidence.pixels * .001,
          `${vp.name}: hiding reconstructed geometry changes pixels and restores the same frame`);
        check(!row.confidence.withoutChannel && !row.confidence.wrongGrade, `${vp.name}: buildings and infrastructure retain reconstructed channels`);
        check(!row.confidence.hiddenPick && !row.confidence.hiddenLayerPick,
          `${vp.name}: hidden context cannot intercept inspection`);
        check(row.confidence.pick?.record?.sidecar?.placement?.position_confidence === 'reconstructed'
          && /libert/i.test(row.confidence.pick.record.sidecar.research_note ?? ''), `${vp.name}: picked context building names its liberties`);
        const citations = row.confidence.pick?.record?.sidecar?.citations ?? [];
        check(citations.length >= 3 && citations.every(c => c.source_id && c.citation && /^https?:\/\//.test(c.url || c.archived_url || '')),
          `${vp.name}: context card supplies real, linked bounding-source citations`);
        row.card = await page.evaluate(async () => {
          const a = window.__chicago4d, hit = a.pick();
          if (hit) await Promise.all([a.pictures(), a.readerText(), a.loadLiberties()]);
          const card = document.getElementById('popup');
          return { id: hit?.id, openId: a.popup.openId, hidden: card?.hidden,
            text: card?.textContent ?? '', citationLinks: card?.querySelectorAll('.cites a[href]').length ?? 0,
            horizontalOverflow: document.documentElement.scrollWidth > innerWidth };
        });
        check(row.card.id?.startsWith('context:1871:') && row.card.openId === row.card.id && !row.card.hidden
          && /reconstructed/i.test(row.card.text)
          && row.card.text.includes('A complete context city on the afternoon before the Great Fire')
          && !row.card.text.includes('No liberties are recorded against this building') && row.card.citationLinks >= 3 && !row.card.horizontalOverflow,
          `${vp.name}: actual app opens a readable, graded context card with liberties`);
        await page.screenshot({ path: path.join(opts.out, `${vp.name}-context-card.png`), timeout: 90_000 });
        await page.evaluate(() => window.__chicago4d.popup.close());

        row.streetWalk = await page.evaluate(() => {
          const a = window.__chicago4d, q = window.__city1871Read, doc = a.contextCity.doc;
          const surfaces = doc.walk_surfaces ?? [], heights = doc.surface_heights_m;
          if (!surfaces.length || !heights || typeof a.contextCity.floorHeight !== 'function') return { error: 'No declared street floors or context floor query' };
          const at = (r, t) => r.a.map((v, i) => v + (r.b[i] - v) * t);
          const covers = (r, p) => {
            const dx = r.b[0] - r.a[0], dy = r.b[1] - r.a[1], length2 = dx * dx + dy * dy;
            const t = ((p[0] - r.a[0]) * dx + (p[1] - r.a[1]) * dy) / length2;
            return t >= 0 && t <= 1 && Math.abs((p[0] - r.a[0]) * dy - (p[1] - r.a[1]) * dx) <= r.width_m / 2 * Math.sqrt(length2);
          };
          const declaredFloor = p => Math.max(heights.ground, ...surfaces.filter(r => covers(r, p)).map(r => r.y));
          const clear = p => !a.terrain.isWater(...p) && !a.contextCity.containsBuilding(...p, a.walkBudget.radius + .1)
            && Math.abs(a.terrain.surfaceHeight(...p) - heights.ground) < .01
            && !(doc.walk_decks ?? []).some(d => p[0] >= Math.min(...d.pts.map(v => v[0])) && p[0] <= Math.max(...d.pts.map(v => v[0]))
              && p[1] >= Math.min(...d.pts.map(v => v[1])) && p[1] <= Math.max(...d.pts.map(v => v[1])));
          const byId = new Map(surfaces.map(r => [r.id, r]));
          const roads = surfaces.filter(r => r.kind === 'road').toSorted((x, y) => Math.hypot(...at(x, .5)) - Math.hypot(...at(y, .5)));
          let chosen = null;
          for (const road of roads) {
            for (const side of [-1, 1]) {
              const walk = byId.get(road.id.replace(/_road$/, `_walk_${side}`));
              if (!walk || walk.kind !== 'walk') continue;
              for (const t of [.5, .37, .63]) {
                const start = at(road, t), end = at(walk, t), distance = Math.hypot(end[0] - start[0], end[1] - start[1]);
                const count = Math.ceil(distance / .16);
                const path = Array.from({ length: count + 1 }, (_, i) => start.map((v, k) => v + (end[k] - v) * i / count));
                if (!path.every(clear) || Math.abs(declaredFloor(start) - road.y) > .001 || Math.abs(declaredFloor(end) - walk.y) > .001) continue;
                chosen = { road, walk, start, end, distance }; break;
              }
              if (chosen) break;
            }
            if (chosen) break;
          }
          if (!chosen) return { error: 'No unobstructed road-to-plank-walk crossing found' };
          const { road, walk, start, end, distance } = chosen;
          a.setFly(false); a.walker.teleport({ local_e: start[0], local_n: start[1] });
          const read = () => { const s = a.walker.state; return { e: s.e, n: s.n, groundY: s.groundY, eyeY: s.eyeY }; };
          const before = read(), outbound = q.stepToward(end, Math.ceil(distance / .16)), onWalk = read();
          const inbound = q.stepToward(start, Math.ceil(distance / .16)), returned = read();
          const samples = [before, ...outbound, onWalk, ...inbound, returned].map(s => ({ ...s, expectedFloor: declaredFloor([s.e, s.n]) }));
          return { roadId: road.id, walkId: walk.id, roadY: road.y, walkY: walk.y, start, end, samples,
            before, onWalk, returned, eyeHeight: a.walkBudget.eyeHeight, stepUp: a.walkBudget.stepUp,
            contextRoadY: a.contextCity.floorHeight(...start), contextWalkY: a.contextCity.floorHeight(...end),
            reachedWalk: Math.hypot(onWalk.e - end[0], onWalk.n - end[1]) < .3,
            returnedToRoad: Math.hypot(returned.e - start[0], returned.n - start[1]) < .3 };
        });
        const streetWalk = row.streetWalk;
        check(!streetWalk.error && streetWalk.walkY > streetWalk.roadY && streetWalk.walkY - streetWalk.roadY <= streetWalk.stepUp
          && streetWalk.reachedWalk && streetWalk.returnedToRoad
          && Math.abs(streetWalk.contextRoadY - streetWalk.roadY) < .005 && Math.abs(streetWalk.contextWalkY - streetWalk.walkY) < .005
          && Math.abs(streetWalk.before.groundY - streetWalk.roadY) < .005 && Math.abs(streetWalk.onWalk.groundY - streetWalk.walkY) < .005
          && Math.abs(streetWalk.returned.groundY - streetWalk.roadY) < .005
          && streetWalk.samples.every(s => Math.abs(s.groundY - s.expectedFloor) < .005 && Math.abs(s.eyeY - s.groundY - streetWalk.eyeHeight) < .01),
          `${vp.name}: actual walker steps from a rendered road onto its plank walk and back with feet on both surfaces${streetWalk.error ? `; ${streetWalk.error}` : ''}`);

        row.bridges = [];
        const decks = (doc.walk_decks ?? []).filter(deck => (deck.kind ?? 'bridge') === 'bridge');
        const centers = decks.map(d => d.pts.reduce((p, q) => [p[0] + q[0] / d.pts.length, p[1] + q[1] / d.pts.length], [0, 0]));
        check(decks.length >= 15 && centers.some(p => p[1] > 500) && centers.some(p => p[1] < -500)
          && centers.some(p => p[0] > 200 && p[1] >= 0 && p[1] < 300), `${vp.name}: bridges reach all three river divisions`);
        for (const deck of decks) {
          const axis = deckAxis(deck);
          const reading = await page.evaluate(({ deck, axis }) => {
            const a = window.__chicago4d, q = window.__city1871Read;
            const center = axis.start.map((v, i) => (v + axis.end[i]) / 2);
            const traversals = [];
            for (const [start, end] of [[axis.start, axis.end], [axis.end, axis.start]]) {
              a.setFly(false); a.walker.teleport({ local_e: start[0], local_n: start[1] });
              const samples = q.stepToward(end, Math.ceil(axis.length / .16));
              const s = a.walker.state;
              traversals.push({ start, end, samples, remaining: Math.hypot(s.e - end[0], s.n - end[1]) });
            }
            return { id: deck.id, deckY: deck.y, eyeHeight: a.walkBudget.eyeHeight, traversals,
              centerWater: a.terrain.isWater(...center), centerHeight: a.walker.surfaceAt(...center) };
          }, { deck, axis });
          row.bridges.push(reading);
          check(reading.centerWater && Math.abs(reading.centerHeight - deck.y) < .02
            && reading.traversals.every(t => t.remaining < .6 && t.samples.every(s => Math.abs(s.eyeY - s.groundY - reading.eyeHeight) < .01)),
          `${vp.name}: real walker crosses ${deck.id} in both directions on its deck`);
        }
        row.quays = await page.evaluate(decks => {
          const a = window.__chicago4d, q = window.__city1871Read;
          return decks.map(deck => {
            const points = deck.pts ?? [], path = deck.access_path ?? [];
            if (points.length < 3 || path.length < 2) return { id: deck.id, error: 'No floor polygon or dry-land access path' };
            const center = points.reduce((p, v) => [p[0] + v[0] / points.length, p[1] + v[1] / points.length], [0, 0]);
            const floor = a.walker.surfaceAt(...center);
            const start = path[0];
            const dryStart = !a.terrain.isWater(...start) && a.terrain.surfaceHeight(...start) >= deck.y - a.walkBudget.stepUp;
            a.setFly(false); a.walker.teleport({ local_e: start[0], local_n: start[1] });
            let feetSupported = true;
            for (const target of path.slice(1)) {
              const s = a.walker.state, length = Math.hypot(target[0] - s.e, target[1] - s.n);
              const samples = q.stepToward(target, Math.ceil(length / .16));
              feetSupported &&= samples.every(p => Math.abs(p.eyeY - p.groundY - a.walkBudget.eyeHeight) < .01);
            }
            const s = a.walker.state, end = path.at(-1);
            return { id: deck.id, center, y: deck.y, floor, dryStart, feetSupported,
              remaining: Math.hypot(s.e - end[0], s.n - end[1]), finalFloor: s.groundY };
          });
        }, (doc.walk_decks ?? []).filter(deck => deck.kind === 'quay'));
        const failedQuays = row.quays.filter(q => q.error || !q.dryStart || !q.feetSupported || q.remaining >= .6
          || Math.abs(q.floor - q.y) > .03 || Math.abs(q.finalFloor - q.y) > .03);
        check(row.quays.length > 0 && !failedQuays.length,
          `${vp.name}: all ${row.quays.length} quay floors support actual entry from dry land${failedQuays.length ? `; failed: ${failedQuays.slice(0, 8).map(q => q.id).join(', ')}` : ''}`);
        row.collision = await page.evaluate(({ b, stand }) => {
          const a = window.__chicago4d, q = window.__city1871Read;
          const start = stand.eye.slice(0, 2), distance = Math.hypot(start[0] - b.e, start[1] - b.n);
          a.setFly(false); a.walker.teleport({ local_e: start[0], local_n: start[1] });
          a.contextCity.update(0, a.camera);
          const before = [a.walker.state.e, a.walker.state.n];
          const samples = q.stepToward([b.e, b.n], Math.ceil((distance + 2) / .16));
          const state = a.walker.state;
          return { id: b.id, before, final: [state.e, state.n], samples,
            moved: Math.hypot(state.e - before[0], state.n - before[1]),
            inside: a.contextCity.containsBuilding(state.e, state.n, 0),
            nearby: a.contextCity.footprintsNear(state.e, state.n).length,
            centreDistance: Math.hypot(state.e - b.e, state.n - b.n), minHalfSpan: Math.min(b.width_m, b.depth_m) / 2 };
        }, { b: subjects.residential, stand: stands.find(s => s.name === 'residential') });
        check(!row.collision.inside && row.collision.centreDistance >= row.collision.minHalfSpan
          && row.collision.moved > .1 && row.collision.nearby > 0 && row.collision.nearby < 500,
          `${vp.name}: nearby house walls stop the actual walker without a whole-city collision scan`);
        const centerOf = deck => deck.pts.reduce((p, v) => [p[0] + v[0] / deck.pts.length, p[1] + v[1] / deck.pts.length], [0, 0]);
        const bridgeView = decks.find(d => d.id === 'state_street_bridge') ?? decks[0];
        const quayView = (doc.walk_decks ?? []).filter(d => d.kind === 'quay').toSorted((a, b) => {
          const ca = centerOf(a), cb = centerOf(b);
          return Math.hypot(ca[0] - 550, ca[1]) - Math.hypot(cb[0] - 550, cb[1]);
        })[0];
        for (const [name, deck, offset] of [['bridge', bridgeView, [-120, -90, 80]], ['quay', quayView, [-35, -32, 28]]]) {
          if (!deck) continue;
          const center = centerOf(deck);
          const reading = await page.evaluate(spec => {
            const a = window.__chicago4d, q = window.__city1871Read;
            return { ...q.summarize(q.stand(spec)), detail: a.detail };
          }, { eye: [center[0] + offset[0], center[1] + offset[1], offset[2]], target: [...center, deck.y] });
          row.frames.push({ tier: reading.detail, stand: name, deckId: deck.id, ...reading });
          check(reading.stats.withinBudget && reading.nonBlackShare > .3 && reading.luminanceRange > 20,
            `${vp.name}/${name}: oblique infrastructure view renders within the declared budget`);
          await page.screenshot({ path: path.join(opts.out, `${vp.name}-${name}.png`), timeout: 90_000 });
        }
        const cdp = await ctx.newCDPSession(page);
        await cdp.send('HeapProfiler.collectGarbage');
        row.chromiumHeap = await cdp.send('Runtime.getHeapUsage');
        row.final = await page.evaluate(() => ({ problems: window.__chicago4d.problems,
          detail: window.__chicago4d.detail, census: window.__chicago4d.contextCity.census, stats: window.__chicago4d.stats() }));
        row.maxFrame = { driverDraws: Math.max(...row.frames.map(f => f.stats.drawCalls)),
          triangles: Math.max(...row.frames.map(f => f.stats.triangles)),
          submittedBuildingInstances: Math.max(...row.frames.map(f => f.census.visibleBuildings)) };
        check(row.final.problems.length === 0, `${vp.name}: no app-reported layer problems`);
        if (opts.portal) {
          // Optional presentation evidence, after the viewport's measurements.
          // Two raw canvas captures in this browser; no UI or image synthesis.
          fs.mkdirSync(opts.portal, { recursive: true });
          await page.setViewportSize({ width: 1280, height: 800 });
          row.portal = [];
          for (const name of ['whole-city', 'river']) {
            const capture = await page.evaluate(id => {
              const a = window.__chicago4d;
              if (id === 'whole-city') a.goTo('whole_city');
              else {
                a.setFly(true); a.walker.teleport({ local_e: -1300, local_n: -900,
                  altitude_m: 450, yaw_deg: 65, pitch_deg: -26 });
              }
              a.step(); a.step();
              return { image: a.renderer.domElement.toDataURL('image/jpeg', .9),
                sun: a.world.describe(), camera: { ...a.walker.enu }, stats: a.stats() };
            }, name);
            const file = path.resolve(opts.portal, `${name}.jpg`);
            fs.writeFileSync(file, Buffer.from(capture.image.split(',')[1], 'base64'));
            delete capture.image;
            row.portal.push({ file, ...capture });
          }
        }
      } catch (error) { check(false, `${vp.name}: ${error.stack || error}`); }
      finally {
        check(row.errors.length === 0, `${vp.name}: zero page errors`);
        check(row.failedResponses.length === 0 && row.failedRequests.length === 0, `${vp.name}: zero failed resource loads`);
        await ctx.close();
        fs.writeFileSync(path.join(opts.out, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
      }
    }
    check(JSON.stringify(snapshot()) === JSON.stringify(report.snapshot), 'published inputs stayed unchanged throughout the reading');
    fs.writeFileSync(path.join(opts.out, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
  } finally { await browser.close(); await new Promise(resolve => server.close(resolve)); }
  console.log(`1871 city ${report.failures.length ? 'FAIL' : 'PASS'} — ${opts.viewport}; tiers ${opts.tiers.join(',')}${report.completeDetailCoverage ? '' : ' (partial detail reading)'} — ${opts.out}/report.json`);
  if (report.failures.length) process.exitCode = 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv.includes('--self-test')) selfTest();
  else await run(parseArgs(process.argv.slice(2)));
}
