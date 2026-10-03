#!/usr/bin/env node
/** Targeted T-2015 published integration review, NOT complete smoke stages.
 * --root PATH is the published site root containing 4d/walk/index.html.
 * --out PATH receives review.json and screenshots. --viewport both|desktop|mobile.
 * No browser is started until this script is explicitly executed.
 */
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { execSync } from 'node:child_process';

const args = process.argv.slice(2);
const option = (key, fallback) => args.includes(key) ? args[args.indexOf(key) + 1] : fallback;
const ROOT = path.resolve(option('--root', '../../site'));
const OUT = path.resolve(option('--out', '/tmp/t2015-final-focused-review'));
const VIEW = option('--viewport', 'both');
const READY_MS = Number(option('--ready-ms', '300000'));
if (!['both', 'desktop', 'mobile'].includes(VIEW)) throw new Error('Invalid --viewport');
await mkdir(OUT, { recursive: true });
const loaded = await import(pathToFileURL(path.join((process.env.NODE_PATH || execSync('npm root -g', { encoding: 'utf8' }).trim()).split(path.delimiter)[0], 'playwright/index.js')).href);
const { chromium } = loaded.chromium ? loaded : loaded.default;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.geojson': 'application/json', '.glb': 'model/gltf-binary', '.bin': 'application/octet-stream', '.wasm': 'application/wasm', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.webmanifest': 'application/manifest+json' };
const server = createServer(async (req, res) => {
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    if (pathname === '/favicon.ico') { res.writeHead(204).end(); return; }
    let file = path.resolve(ROOT, `.${pathname}`);
    if (file !== ROOT && !file.startsWith(ROOT + path.sep)) { res.writeHead(403).end(); return; }
    if (pathname.endsWith('/')) file = path.join(file, 'index.html');
    const bytes = await readFile(file);
    res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
    res.end(bytes);
  } catch { res.writeHead(404).end('Not found'); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const ENTRY_URL = `http://127.0.0.1:${server.address().port}/4d/walk/?year=1835`;
const poses = [
  ['prairie', { local_e: -250, local_n: -150, yaw_deg: 90, pitch_deg: -8 }],
  ['woodland-close', { local_e: -186, local_n: 692, yaw_deg: 90, pitch_deg: -8 }],
];
const configs = [
  { name: 'desktop', viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1, hasTouch: false, isMobile: false },
  { name: 'mobile', viewport: { width: 390, height: 780 }, deviceScaleFactor: 2, hasTouch: true, isMobile: false },
].filter(c => VIEW === 'both' || VIEW === c.name);
const result = { scope: 'Targeted published vegetation, material, held confidence off/on/off restoration and disclosure checks, using manual production api.step frames with animation held. Includes the current stock stage2 traced-river/fallback gate and an aerial nonblack frame with confidence/hide uniforms off; no invented pixel-contrast threshold. Not complete smoke stages 2/5/9/10/11/12/13 and no FPS or continuous walk claim. Shadow parity inspects real materials and generated shader code; complete shadow behaviour remains stage 9.', root: ROOT, started: new Date().toISOString(), viewports: [], errors: [] };
const save = () => writeFile(path.join(OUT, 'review.json'), JSON.stringify(result, null, 2));
const fingerprintFiles = ['main.js', 'flora.js', 'trees.js', 'tree-surface.js', 'foliage-atlas.js', 'shrub-grain.js'];
const fingerprints = async () => Object.fromEntries(await Promise.all(fingerprintFiles.map(async file => [file, createHash('sha256').update(await readFile(path.join(ROOT, '4d/walk/js', file))).digest('hex')])));
function delta(a, b) {
  if (!a?.cells?.length || a.cells.length !== b?.cells?.length) return { mean: Infinity, worst: Infinity };
  const values = a.cells.map((v, i) => Math.abs(v - b.cells[i]));
  return { mean: values.reduce((a, b) => a + b, 0) / values.length, worst: Math.max(...values) };
}
try {
  result.provenance = {
    baseDev: option('--base-dev', null),
    publication: 'The published build label may identify a checkpoint before uncommitted integration changes. SHA256 fingerprints identify the actual published modules under review.',
    build: JSON.parse(await readFile(path.join(ROOT, '4d/build.json'), 'utf8')),
    sha256: await fingerprints(),
  };
  await save();
  for (const config of configs) {
    const { name, ...contextOptions } = config;
    const record = { name, config: contextOptions, checks: [], frames: [], tiers: [], errors: [] };
    result.viewports.push(record);
    const check = (label, pass, evidence) => {
      record.checks.push({ label, pass: !!pass, evidence });
      console.log(`${pass ? 'PASS' : 'FAIL'} ${name}: ${label} ${JSON.stringify(evidence)}`);
    };
    const mark = async message => { record.phase = message; record.updated = new Date().toISOString(); console.log(`${record.updated} ${name}: ${message}`); await save(); };
    let browser;
    try {
      await mark('launch');
      browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--enable-unsafe-swiftshader'], timeout: READY_MS });
      const context = await browser.newContext(contextOptions);
      const page = await context.newPage();
      page.setDefaultTimeout(READY_MS);
      page.on('pageerror', e => record.errors.push(`pageerror: ${e.message}`));
      page.on('console', m => { if (m.type() === 'error') record.errors.push(`console.error: ${m.text()}`); });
      page.on('response', r => { if (r.status() >= 400) record.errors.push(`HTTP ${r.status()} ${r.url()}`); });
      page.on('requestfailed', r => { const reason = r.failure()?.errorText || ''; if (!/ERR_ABORTED/.test(reason)) record.errors.push(`requestfailed: ${reason} ${r.url()}`); });
      await page.addInitScript(() => { localStorage.setItem('chicago4d.detail', 'full'); localStorage.setItem('chicago4d.entered', '1'); });
      const started = Date.now();
      await mark('load published entry');
      const response = await page.goto(ENTRY_URL, { waitUntil: 'domcontentloaded', timeout: READY_MS });
      check('published entry responds', response?.status() === 200, response?.status());
      await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: READY_MS, polling: 500 });
      record.readyMs = Date.now() - started;
      await mark(`ready in ${record.readyMs} ms`);
      const device = await page.evaluate(() => {
        const a = window.__chicago4d;
        a.setAnimationHold(true); a.renderer.setAnimationLoop(null);
        if (a.welcome?.state !== 'world') a.welcome?.enter('spawn');
        document.getElementById('control-help-gotit')?.click();
        document.exitPointerLock?.(); a.popup.close(); a.hud.setPanel(false);
        return { dpr: devicePixelRatio, width: innerWidth, height: innerHeight, touchPoints: navigator.maxTouchPoints, coarsePointer: matchMedia('(pointer: coarse)').matches, detail: a.detail, hardProblems: a.problems.filter(p => !/provisional|PLACEHOLDER|placeholder|review_required is set/i.test(p)) };
      });
      record.device = device;
      check('requested viewport and DPR are real', device.width === config.viewport.width && device.height === config.viewport.height && device.dpr === config.deviceScaleFactor, device);
      check('actual touch mobile configuration', name !== 'mobile' || (device.touchPoints > 0 && device.coarsePointer), device);
      check('no unexpected loader problems', device.hardProblems.length === 0, device.hardProblems);
      const capture = async () => page.evaluate(() => { const a = window.__chicago4d; const pending = a.capture(); a.step(); return pending; });
      const screenshot = async label => {
        const filename = `${name}-${label}.jpg`;
        await page.screenshot({ path: path.join(OUT, filename), type: 'jpeg', quality: 88 });
        return filename;
      };
      for (const [label, pose] of poses) {
        await mark(`frame ${label}`);
        const snapshot = await page.evaluate(p => {
          const a = window.__chicago4d; a.setFly(false); a.walker.teleport(p); a.step();
          return { detail: a.detail, stats: a.stats(), zone: a.flora.zoneAt(p.local_e, p.local_n) };
        }, pose);
        const signature = await capture();
        check(`${label} draws a non-black frame`, signature.mean > 12 && signature.litFraction > 0.5, { mean: signature.mean, litFraction: signature.litFraction, width: signature.width, height: signature.height });
        record.frames.push({ label, pose, detail: snapshot.detail, zone: snapshot.zone, drawCalls: snapshot.stats.drawCalls, triangles: snapshot.stats.triangles, signature, screenshot: await screenshot(label) });
        await save();
      }
      // Fixed woodland view is rich in the changed surfaces; hold the clock and
      // manually drive production frames so unrelated background renders cannot
      // create either the confidence difference or a restore residual.
      await mark('confidence off/on/off');
      await page.evaluate(() => window.__chicago4d.setConfidenceView(false));
      const off = await capture();
      await page.evaluate(() => window.__chicago4d.setConfidenceView(true));
      const on = await capture();
      await screenshot('woodland-confidence-on');
      await page.evaluate(() => window.__chicago4d.setConfidenceView(false));
      const back = await capture();
      record.confidence = { changed: delta(off, on), restored: delta(off, back), off, on, back };
      check('confidence changes the held woodland render', record.confidence.changed.worst >= 6 && record.confidence.changed.mean >= 0.6, record.confidence.changed);
      check('confidence off restores the held render', record.confidence.restored.mean <= 0.1 && record.confidence.restored.worst <= 3, record.confidence.restored);
      await save();

      await mark('current stock traced-river gate and aerial confidence-off frame');
      const aerial = await page.evaluate(() => {
        const a = window.__chicago4d;
        a.setConfidenceView(false); a.goTo('from_above'); a.step();
        let water = null, groundTiles = 0;
        a.scene3d.traverse(o => {
          if (!o.isMesh) return;
          if (/^water__/.test(o.name || '')) water = o;
          if (/^terrain__/.test(o.name || '')) groundTiles++;
        });
        let box = null;
        if (water) {
          water.geometry.computeBoundingBox();
          const b = water.geometry.boundingBox;
          box = { w: +(b.max.x - b.min.x).toFixed(1), d: +(b.max.z - b.min.z).toFixed(1) };
        }
        const u = a.confidence.uniforms, hidden = u.uHideLevel.value;
        return { box, groundTiles, terrainProblems: a.problems.filter(t => /^\s*(terrain|water)\b/i.test(t)), confMode: u.uConfMode.value, hideLevel: [hidden.x, hidden.y, hidden.z], flying: a.walker.state.flying, altitude: a.walker.state.altitude };
      });
      const aerialSignature = await capture();
      record.aerialConfidenceOff = { ...aerial, signature: aerialSignature };
      check('stock traced river loaded rather than the flat fallback', aerial.box !== null && aerial.box.w > 3000 && aerial.box.d > 3000 && aerial.groundTiles > 1, aerial);
      check('terrain and river report no load problems', aerial.terrainProblems.length === 0, aerial.terrainProblems);
      check('aerial confidence and hiding are switched off', aerial.confMode === 0 && aerial.hideLevel.every(v => v === 0) && aerial.flying && aerial.altitude > 100, aerial);
      check('aerial off frame is non-black at stock numeric bars', aerialSignature.mean > 12 && aerialSignature.litFraction > 0.5, { mean: aerialSignature.mean, litFraction: aerialSignature.litFraction });
      await save();

      const tierSnapshot = async level => {
        await mark(`tier ${level}`);
        return page.evaluate(async ({ level, pose }) => {
          const a = window.__chicago4d;
          if (a.detail !== level) await a.setDetail(level);
          a.setAnimationHold(true); a.renderer.setAnimationLoop(null); a.setFly(false); a.walker.teleport(pose); a.step();
          const near = a.flora.group.getObjectByName('flora-shrub');
          const far = a.flora.group.getObjectByName('flora-shrub-far');
          if (!near || !far) throw new Error('Near or far shrub mesh is missing');
          const key = (m, i) => [12, 13, 14].map(j => m.instanceMatrix.array[i * 16 + j].toFixed(5)).join(',');
          const farSlots = new Map(Array.from({ length: far.count }, (_, i) => [key(far, i), i]));
          let matched = 0, worst = 0, handoverWorst = 0;
          for (let i = 0; i < near.count; i++) {
            const j = farSlots.get(key(near, i)); if (j === undefined) continue;
            matched++;
            for (const [n, p, q, stride] of [['matrix', near.instanceMatrix, far.instanceMatrix, 16], ['colour', near.instanceColor, far.instanceColor, 3], ...['aFlora', '_confidence', 'aChiFamily'].map(n => [n, near.geometry.getAttribute(n), far.geometry.getAttribute(n), near.geometry.getAttribute(n).itemSize])]) {
              for (let k = 0; k < stride; k++) worst = Math.max(worst, Math.abs(p.array[i * stride + k] - q.array[j * stride + k]));
            }
            const nr = near.geometry.getAttribute('aChiRing'), fr = far.geometry.getAttribute('aChiRing');
            handoverWorst = Math.max(handoverWorst, Math.abs(fr.getZ(j) - (nr.getX(i) - nr.getY(i))));
          }
          const mock = material => {
            const shader = { uniforms: {}, vertexShader: ['beginnormal_vertex', 'color_vertex', 'begin_vertex', 'project_vertex'].map(s => `#include <${s}>`).join('\n'), fragmentShader: ['clipping_planes_fragment', 'color_fragment', 'normal_fragment_begin', 'normal_fragment_maps', 'roughnessmap_fragment', 'lights_fragment_end', 'opaque_fragment'].map(s => `#include <${s}>`).join('\n') };
            material.onBeforeCompile(shader, a.renderer); return shader;
          };
          const ns = mock(near.material), fs = mock(far.material), atlas = ns.uniforms.uChiFoliage?.value;
          const gl = a.renderer.getContext();
          const programs = [...new Set([near.material, far.material, a.flora.group.getObjectByName('flora-mid').material])].map(material => {
            const program = a.renderer.properties.get(material).currentProgram?.program;
            if (!program) return { linked: false, slots: null };
            const attributes = [];
            for (let i = 0; i < gl.getProgramParameter(program, gl.ACTIVE_ATTRIBUTES); i++) {
              const attr = gl.getActiveAttrib(program, i);
              const columns = attr.type === gl.FLOAT_MAT4 ? 4 : attr.type === gl.FLOAT_MAT3 ? 3 : attr.type === gl.FLOAT_MAT2 ? 2 : 1;
              attributes.push({ name: attr.name, size: attr.size, columns });
            }
            return { linked: gl.getProgramParameter(program, gl.LINK_STATUS), slots: attributes.reduce((n, x) => n + x.size * x.columns, 0), attributes };
          });
          const timber = a.trees.group.getObjectByName('timber');
          if (!timber) throw new Error('Timber batch missing');
          const mats = [timber.material, timber.customDepthMaterial, timber.customDistanceMaterial];
          if (mats.some(m => !m)) throw new Error('Tree surface/depth/distance material missing');
          const shaders = mats.map(mock);
          const windBlock = s => s.vertexShader.match(/vec3 chiW[\s\S]*?transformed\.z \+= chiS \* aFlex \* 0\.26;/)?.[0] ?? null;
          return {
            level: a.detail, near: near.count, far: far.count, nearTriangles: near.geometry.index.count / 3, farTriangles: far.geometry.index.count / 3, matched, worst, handoverWorst,
            sharedAtlas: !!atlas && atlas === fs.uniforms.uChiFoliage?.value, atlasSize: atlas ? [atlas.image.width, atlas.image.height] : null,
            packed: [near, far].map(m => ({ dir: m.geometry.getAttribute('aDir')?.itemSize, side: m.geometry.getAttribute('aSide')?.itemSize, family: m.geometry.getAttribute('aChiFamily')?.itemSize })),
            programs, maxAttributes: gl.getParameter(gl.MAX_VERTEX_ATTRIBS),
            tree: { atlasSize: [mats[0].map.image.width, mats[0].map.image.height], sharedMap: mats.every(m => m.map === mats[0].map), cutoff: mats.map(m => m.alphaTest), windUniformShared: shaders.every(s => s.uniforms.uWind === shaders[0].uniforms.uWind) && !!shaders[0].uniforms.uWind, windCodeEqual: !!windBlock(shaders[0]) && shaders.every(s => windBlock(s) === windBlock(shaders[0])), confidencePatched: shaders.every(s => s.vertexShader.includes('attribute float _confidence') && s.fragmentShader.includes('uConfMode')), cutout: mats.every(m => m.transparent === false && m.depthWrite === true) },
            signature: [near, far].map(m => Array.from({ length: m.count }, (_, i) => key(m, i)).sort()),
          };
        }, { level, pose: poses[1][1] });
      };
      for (const level of ['full', 'light', 'full']) {
        const row = await tierSnapshot(level); record.tiers.push(row);
        check(`${level}: populated near/far shrubs share one plant`, row.near > 0 && row.far > 0 && row.matched > 0 && row.worst < 1e-5 && row.handoverWorst < 1e-4, { near: row.near, far: row.far, matched: row.matched, worst: row.worst, handoverWorst: row.handoverWorst });
        check(`${level}: far shrub remains 48 triangles`, row.farTriangles === 48 && row.nearTriangles === (level === 'light' ? 136 : 520), { near: row.nearTriangles, far: row.farTriangles });
        check(`${level}: shared understory atlas and packed attributes`, row.sharedAtlas && String(row.atlasSize) === '512,2048' && row.packed.every(p => p.dir === 4 && p.side === 4 && p.family === 1) && row.programs.every(p => p.linked && p.slots <= 16), { atlas: row.atlasSize, packed: row.packed, programs: row.programs, maxAttributes: row.maxAttributes });
        check(`${level}: tree colour/depth/distance share cutout and wind`, row.tree.sharedMap && String(row.tree.atlasSize) === '2048,2048' && row.tree.cutoff.every(v => v === 0.38) && row.tree.windUniformShared && row.tree.windCodeEqual && row.tree.confidencePatched && row.tree.cutout, row.tree);
        await save();
      }
      check('full-light-full restores the full shrub census', JSON.stringify(record.tiers[0].signature) === JSON.stringify(record.tiers[2].signature), { first: [record.tiers[0].near, record.tiers[0].far], restored: [record.tiers[2].near, record.tiers[2].far] });
      // Existing HUD entry points exercise real lazy imports/panel rendering.
      // This deliberately does not re-test unchanged unread-state persistence.
      await mark('disclosures');
      await page.evaluate(() => { const a = window.__chicago4d; a.popup.close(); a.hud.setPanel(true); a.hud.selectTab('whatsnew'); });
      await page.waitForFunction(() => document.querySelector('#whatsnew .wn-title'), null, { polling: 100, timeout: READY_MS });
      const news = await page.evaluate(async () => {
        const { CHANGELOG } = await import(new URL('./js/changelog.js', location.href).href);
        const host = document.querySelector('#whatsnew'), title = host.querySelector('.wn-title');
        title.scrollIntoView({ block: 'center' });
        const panel = host.closest('.panel-body');
        return { latest: CHANGELOG[0].title, rendered: title.textContent, date: host.querySelector('.wn-meta')?.textContent, active: window.__chicago4d.hud.tab === 'whatsnew' && !panel?.hasAttribute('hidden'), count: host.querySelectorAll('.wn-entry').length };
      });
      check('latest published changelog renders in its tab', news.active && news.latest === news.rendered && /CT/.test(news.date || '') && news.count > 0, news);
      record.news = news;
      await screenshot('whatsnew');
      await save();
      await page.evaluate(() => { const a = window.__chicago4d; a.hud.selectTab('evidence'); a.evidenceHub.showTopic('liberties'); });
      await page.waitForFunction(() => [...document.querySelectorAll('#liberties details.lib')].some(e => /\bL369\b/.test(e.textContent)), null, { polling: 100, timeout: READY_MS });
      const liberty = await page.evaluate(() => {
        const row = [...document.querySelectorAll('#liberties details.lib')].find(e => /\bL369\b/.test(e.textContent));
        row.open = true; row.scrollIntoView({ block: 'start' });
        const r = row.getBoundingClientRect();
        return { active: window.__chicago4d.hud.tab === 'evidence', visible: r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight, text: row.textContent.replace(/\s+/g, ' ').trim(), rendered: document.querySelectorAll('#liberties details.lib').length, loaded: window.__chicago4d.liberties?.count };
      });
      check('L369 botanical reconstruction disclosure is visible', liberty.active && liberty.visible && /Leaf.scale procedural vegetation/.test(liberty.text) && /visual reconstructions/.test(liberty.text) && liberty.rendered === liberty.loaded, liberty);
      await screenshot('liberty-L369');
      record.liberty = liberty;
      record.finalSha256 = await fingerprints();
      check('published reviewed modules stayed unchanged throughout viewport', JSON.stringify(record.finalSha256) === JSON.stringify(result.provenance.sha256), record.finalSha256);
      check('zero page, console and resource errors', record.errors.length === 0, record.errors);
    } catch (e) {
      record.errors.push(e.stack || String(e));
      check('targeted review completed', false, e.message || String(e));
    } finally {
      await browser?.close();
      record.pass = record.errors.length === 0 && record.checks.length > 0 && record.checks.every(c => c.pass);
      await save();
    }
  }
} catch (e) { result.errors.push(e.stack || String(e)); }
finally {
  result.finished = new Date().toISOString();
  result.pass = result.errors.length === 0 && result.viewports.length === configs.length && result.viewports.every(v => v.pass);
  await save();
  await new Promise(resolve => server.close(resolve));
  console.log(JSON.stringify({ pass: result.pass, report: path.join(OUT, 'review.json'), viewports: result.viewports.map(v => ({ name: v.name, pass: v.pass, checks: v.checks.length, errors: v.errors })) }));
  process.exitCode = result.pass ? 0 : 1;
}
