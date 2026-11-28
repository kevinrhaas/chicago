// Fixed-camera published vegetation evidence. QA_BEFORE holds the old JS files;
// only those files are substituted, so both renders use the same assets/data.
// QA_YEAR=1812,1835,1871,1904 QA_VIEWPORT=desktop|mobile QA_TIERS=light,balanced,full
// QA_SEASONS=summer,spring,fall,winter QA_FRAMES=9 (3 for shader/image checks)
// QA_MODES=1 also checks night and Confidence view once per scene/viewport.
// QA_STAND=water_tower|pumping_tree selects a diagnostic 1871 viewpoint.
// QA_TAG=before|after QA_OUT=/path QA_BEFORE=/path/to/old/js PW_EXECUTABLE=... node ...
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url), { chromium } = require('playwright');
const root = path.resolve(new URL('..', import.meta.url).pathname);
const site = path.resolve(root, process.env.QA_SITE || '../../site/4d');
const out = process.env.QA_OUT;
if (!out) throw Error('QA_OUT must name the evidence directory');
fs.mkdirSync(out, { recursive: true });
const tag = process.env.QA_TAG || 'after';
const frames = Math.max(3, Number(process.env.QA_FRAMES || 9));
const stand = process.env.QA_STAND || null;
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json',
  '.css': 'text/css', '.glb': 'model/gltf-binary', '.wasm': 'application/wasm',
  '.webp': 'image/webp', '.ktx2': 'image/ktx2', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg' };
const server = http.createServer((req, res) => {
  let file = path.join(site, decodeURIComponent(req.url.split('?')[0]));
  if (process.env.QA_BEFORE && /\/js\/[^/]+\.js$/.test(file)) {
    const old = path.join(process.env.QA_BEFORE, path.basename(file));
    if (fs.existsSync(old)) file = old;
  }
  try {
    if (fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
    res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    fs.createReadStream(file).pipe(res);
  } catch { res.writeHead(404); res.end('missing'); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const observations = [];
try {
  for (const year of (process.env.QA_YEAR || '1812,1835,1871,1904').split(',')) {
    for (const viewport of ['desktop', 'mobile']) {
      if (process.env.QA_VIEWPORT && process.env.QA_VIEWPORT !== viewport) continue;
      const mobile = viewport === 'mobile';
      const context = await browser.newContext({ viewport: mobile ? { width: 390, height: 780 } : { width: 1280, height: 800 },
        isMobile: mobile, hasTouch: mobile, deviceScaleFactor: 1 });
      const page = await context.newPage();
      page.setDefaultTimeout(400000);
      const errors = [];
      page.on('pageerror', e => { errors.push(String(e)); console.log('pageerror', String(e)); });
      page.on('console', m => {
        if (m.text().startsWith('[vegetation]')) console.log(m.text());
        if (m.type() === 'error' && /THREE.WebGLProgram|GL_INVALID|shader error/i.test(m.text())) {
          errors.push(m.text()); console.log('shader error', m.text().slice(0, 2500));
        }
      });
      console.log(tag, year, viewport, 'booting');
      await page.goto(`http://127.0.0.1:${server.address().port}/${year}/?device=${process.env.QA_DEVICE || (mobile ? 'weak' : 'standard')}`, { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 400000, polling: 500 });
      const boot = await page.evaluate(() => ({ ready: __chicago4d.ready, error: __chicago4d.error,
        welcome: __chicago4d.welcome?.state, problems: __chicago4d.problems?.slice(-5) }));
      console.log(tag, year, viewport, 'boot', JSON.stringify(boot));
      if (boot.error) throw Error(`scene failed to boot: ${JSON.stringify(boot.error)}`);
      // The official smoke holds draws during non-pixel reads (T-2337), keeping
      // arrival/checkpoint ticks running without drawing the town at every tick.
      await page.evaluate(() => {
        const r = __chicago4d.renderer;
        window.__vegetationDraw = r.render;
        r.render = (scene, camera) => camera?.updateMatrixWorld?.();
      });
      await page.waitForFunction(() => window.__chicago4d?.welcome.state === 'welcome', null, { timeout: 400000, polling: 500 });
      console.log(tag, year, viewport, 'welcome');
      await page.evaluate(() => {
        const a = window.__chicago4d;
        if (!a.welcome.enter('spawn')) throw Error('welcome entry failed');
        document.exitPointerLock?.(); document.getElementById('control-help-gotit')?.click();
      });
      await page.waitForFunction(() => document.getElementById('gate').hidden);
      console.log(tag, year, viewport, 'entered');
      await page.evaluate(() => {
        const a = __chicago4d;
        a.renderer.setAnimationLoop(null);
        a.renderer.setPixelRatio(1); // same raster workload for the before/after timing
        a.step();
      });
      const seasons = (process.env.QA_SEASONS || 'summer').split(',');
      const tiers = (process.env.QA_TIERS || 'light,balanced,full').split(',');
      // Hold each tier while exercising every season; this avoids rebuilding
      // the entire placement plan once per season while keeping all cases.
      for (const detail of tiers) {
        await page.evaluate(async detail => {
          const a = __chicago4d;
          a.renderer.render = (scene, camera) => camera?.updateMatrixWorld?.();
          await a.setDetail(detail); a.step();
          a.renderer.render = window.__vegetationDraw;
        }, detail);
        await page.waitForFunction(detail => {
          const a = __chicago4d;
          return [a.streetTrees, a.frontYards].every(layer => {
            if (!layer?.stats?.grown?.stems || layer.stats.mode === 'hidden') return true;
            return layer.stats.detail === detail && layer.group.children.some(o => o.name?.endsWith('s-grown'));
          });
        }, detail);
      for (const season of seasons) {
        await page.evaluate(async season => {
          const a = __chicago4d;
          a.renderer.render = (scene, camera) => camera?.updateMatrixWorld?.();
          await a.season.set(season); a.step();
          if (a.season.current !== season) throw Error(`requested ${season}, got ${a.season.current}`);
          a.renderer.render = window.__vegetationDraw;
        }, season);
        await page.waitForFunction(() => [__chicago4d.streetTrees, __chicago4d.frontYards].every(layer =>
          !layer?.stats?.grown?.stems || layer.stats.mode === 'hidden'
            || layer.group.children.some(o => o.name?.endsWith('s-grown'))));
        console.log(tag, year, viewport, detail, 'built');
        const row = await page.evaluate(({ year, detail, season, frames, stand }) => {
          const a = __chicago4d;
          console.info('[vegetation] positioning');
          const trunks = a.trees?.trunks?.() || [];
          const spawn = a.scene.spawn;
          let eye, target;
          if (year === '1904') { eye = [1401, -3240, 1.7]; target = [1403, -3300, 18]; }
          else if (year === '1871') {
            if (stand === 'water_tower') { eye = [1138, 1084, 1.7]; target = [1150, 1154, 10]; }
            else if (stand === 'pumping_tree') { eye = [1168, 1127.5, 1.7]; target = [1175.08, 1137.74, 6]; }
            else { eye = [901, -573, 1.7]; target = [900, -500, 8]; }
          }
          else {
            const near = trunks.filter(t => t.r > 0.08).sort((p, q) =>
              Math.hypot(p.e - spawn.local_e, p.n - spawn.local_n) - Math.hypot(q.e - spawn.local_e, q.n - spawn.local_n))[0];
            const t = near || { e: spawn.local_e, n: spawn.local_n };
            eye = [t.e - 13, t.n - 16, 1.7]; target = [t.e, t.n, 9];
          }
          const yaw = Math.atan2(target[0] - eye[0], target[1] - eye[1]) * 180 / Math.PI;
          a.setFly(true);
          a.walker.teleport({ local_e: eye[0], local_n: eye[1], altitude_m: eye[2], yaw_deg: yaw, pitch_deg: 10 });
          console.info('[vegetation] stepping');
          a.step();
          console.info('[vegetation] stepped');
          a.camera.position.set(eye[0], a.terrain.surfaceHeight(eye[0], eye[1]) + eye[2], -eye[1]);
          a.camera.lookAt(target[0], a.terrain.surfaceHeight(target[0], target[1]) + target[2], -target[1]);
          a.camera.updateMatrixWorld();
          a.world.follow(a.camera.position); a.world.aim(a.camera);
          a.trees?.update?.(0, a.camera); a.trees?.settle?.();
          a.streetTrees?.update?.(0, a.camera); a.streetTrees?.settle?.();
          a.frontYards?.update?.(0, a.camera); a.contextCity?.update?.(0, a.camera);
          document.getElementById('nav-close')?.click();
          document.getElementById('panel-close')?.click();
          console.info('[vegetation] reading frames');
          const gl = a.renderer.getContext();
          const samples = [];
          for (let i = 0; i < frames; i++) {
            console.info(`[vegetation] frame ${i}`);
            a.renderer.info.reset();
            const t = performance.now();
            a.renderer.render(a.scene3d, a.camera); gl.finish();
            if (i > 1) samples.push(performance.now() - t);
          }
          samples.sort((p, q) => p - q);
          const buffers = new Set(), textures = new Set();
          let geometryBytes = 0;
          a.scene3d.traverse(o => {
            const g = o.geometry;
            for (const attr of [...Object.values(g?.attributes || {}), g?.index]) {
              const array = attr?.isInterleavedBufferAttribute ? attr.data.array : attr?.array;
              if (array && !buffers.has(array.buffer)) { buffers.add(array.buffer); geometryBytes += array.buffer.byteLength; }
            }
            for (const m of [].concat(o.material || [])) for (const v of Object.values(m)) if (v?.isTexture) textures.add(v);
          });
          return { year, detail, season, stand, sunDate: a.season.sunDate, eye, target, triangles: a.renderer.info.render.triangles,
            calls: a.renderer.info.render.calls, memory: { ...a.renderer.info.memory },
            keptGeometryBytes: geometryBytes, materialTextures: textures.size, frameSamples: samples.length,
            frameMs: { median: samples[Math.floor(samples.length / 2)], max: samples.at(-1) },
            pixelRatio: a.renderer.getPixelRatio(), device: a.device, problems: a.problems,
            treeCount: a.trees?.stats?.grown?.stems, streetTreeCount: a.streetTrees?.stats?.grown?.stems };
        }, { year, detail, season, frames, stand });
        console.log('metrics', JSON.stringify({ year, detail, triangles: row.triangles, calls: row.calls, frameMs: row.frameMs }));
        const image = `${tag}-${year}-${viewport}-${detail}-${season}${stand ? `-${stand}` : ''}.jpg`;
        await page.screenshot({ path: path.join(out, image), type: 'jpeg', quality: 90, timeout: 400000 });
        row.image = image; row.viewport = viewport; row.errors = [...errors];
        if (process.env.QA_MODES === '1' && detail === tiers.at(-1) && season === seasons[0]) {
          row.modes = await page.evaluate(async () => {
            const a = __chicago4d, renderer = a.renderer, draw = window.__vegetationDraw;
            const position = a.camera.position.clone(), rotation = a.camera.quaternion.clone();
            const ownTime = a.timeOfDay.current.own, confidence = a.confidenceView;
            const { LEAF_SKY } = await import('/walk/js/time-of-day.js');
            const shot = async () => {
              renderer.render = (scene, camera) => camera?.updateMatrixWorld?.();
              a.step(); a.camera.position.copy(position); a.camera.quaternion.copy(rotation); a.camera.updateMatrixWorld();
              renderer.render = draw; renderer.render(a.scene3d, a.camera); renderer.getContext().finish();
              const bytes = new TextEncoder().encode(renderer.domElement.toDataURL());
              const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(v => v.toString(16).padStart(2, '0')).join('');
              return { hash, leafSky: LEAF_SKY.value, clock: a.timeOfDay.current, confidence: a.confidenceView };
            };
            let day, night, restored, graded;
            a.setAnimationHold(true);
            try {
              day = await shot();
              await a.timeOfDay.set('night'); night = await shot();
              if (!(night.leafSky >= 0 && night.leafSky < day.leafSky) || night.hash === day.hash)
                throw Error('night did not reduce leaf skylight/change the frame');
              await a.timeOfDay.set(ownTime); restored = await shot();
              a.setConfidenceView(!confidence); graded = await shot();
              if (graded.confidence === confidence || graded.hash === restored.hash) throw Error('Confidence view did not change the frame');
            } finally {
              await a.timeOfDay.set(ownTime); a.setConfidenceView(confidence); await shot();
              a.setAnimationHold(false);
              renderer.render = draw;
            }
            return { day, night, restored, graded, note: 'Animation held for single-frame mode/shader checks; hashes are diagnostic, not fidelity or timing measurements.' };
          });
        }
        row.errors = [...errors];
        observations.push(row);
        fs.writeFileSync(path.join(out, `${tag}-${year}-${viewport}.json`), JSON.stringify(observations, null, 2));
        console.log(JSON.stringify({ tag, year, viewport, detail, triangles: row.triangles, calls: row.calls, frameMs: row.frameMs, errors: errors.length }));
        if (errors.length) throw Error(errors.join('\n'));
      }
      }
      await context.close();
    }
  }
} finally { await browser.close(); server.close(); }
