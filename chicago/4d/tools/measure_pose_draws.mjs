/**
 * WHAT ONE FRAME SENDS TO THE GPU AT A READ-FRAME-PACING POSE, LAYER BY LAYER — T-2927.
 *
 *   PW_EXECUTABLE=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \
 *     node tools/measure_pose_draws.mjs [--year 1904] [--pose flight|walk|turn] [--t 0,7.5,15]
 *       [--tier light] [--w 375 --h 636] [--qs coalesce=0] [--no-layers]
 *       [--break structures,railway] [--root ../../site/4d] [--json f]
 *
 * The camera is the one Read frame pacing drives (pacing-read.js SCENE_POSES, `poseFrom`
 * at `--t` seconds into the move), on the PUBLISHED mirror, at the owner's phone
 * profile: a 375x636 touch viewport, ratio 1 (his Sharpness Low), Scene detail light,
 * Fixed pacing. Each frame is the page's own `step()`.
 *
 * WHY IT COUNTS AT THE GL CALL. `renderer.info.render.calls` counts a BatchedMesh as
 * ONE call, but three submits it as a multi-draw with one entry per instance it kept,
 * and each entry is a draw to the driver (ANGLE loops them where the GPU has no native
 * multi-draw). At 1904's flight pose the page reported 339 calls while the GL received
 * 27,895 draws. So every draw, its triangles (x instances) and the framebuffer it went
 * to (0 is the canvas; the other is the sun's map) are counted on the WebGL2 context.
 *
 * Per layer (a named top-level group): hidden for one frame (what it costs at all), then
 * its casters cleared (what the sun costs on it). `finish` is SwiftShader's wall time
 * for the frame with a readPixels: it is NOT a phone's, and is printed only as a
 * relative reading. `--break` lists one group's visible meshes with the draws and
 * triangles each submitted. `--qs coalesce=0` reads the same build without T-2927's
 * joined runs (batch-coalesce.js).
 *
 * T-2970: `page meter` is `__chicago4d.stats().drawCalls`, the driver-draw count every
 * draw budget now reads (driver-draws.js), printed beside the GL's own count of the
 * same frame so the meter is audited by an instrument that does not share its code.
 *
 * A measurement, not a gate.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

const argAt = (n) => { const i = process.argv.indexOf(n); return i >= 0 ? process.argv[i + 1] : null; };
const HERE = path.dirname(new URL(import.meta.url).pathname);
const ROOT = path.resolve(argAt('--root') || path.join(HERE, '../../../site/4d'));
if (!fs.existsSync(path.join(ROOT, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} \u2014 run tools/publish.sh first`);
  process.exit(2);
}
const YEAR = argAt('--year') || '1904';
const POSE = argAt('--pose') || 'flight';
const TS = (argAt('--t') || '0').split(',').map(Number);
const W = Number(argAt('--w') || 375), H = Number(argAt('--h') || 636);
const TIER = argAt('--tier') || 'light';
const QS = argAt('--qs') || '';
const LAYERS = !process.argv.includes('--no-layers');
const jsonOut = argAt('--json');
const BREAK = (argAt('--break') || '').split(',').filter(Boolean);

async function loadPlaywright() {
  let ns;
  try { ns = await import('playwright'); } catch {
    const root = (process.env.NODE_PATH || execSync('npm root -g', { encoding: 'utf8' })).trim().split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.glb': 'model/gltf-binary', '.wasm': 'application/wasm', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.ktx2': 'image/ktx2', '.webp': 'image/webp' };
const PORT = Number(process.env.POSE_PORT || 4291);
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file)) { res.writeHead(404); res.end('nf'); return; }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(PORT, r));

// GL-level tally: every draw, its primitives (x instances), and which framebuffer it went to.
function glTally() {
  const T = { draws: 0, tris: 0, fbDraws: 0, fbTris: 0, clears: 0, binds: 0, perFb: new Map(), fb: null };
  window.__glT = T;
  const fbId = new WeakMap(); let nextFb = 1;
  const note = (count, inst = 1, mode = 4) => {
    const tris = mode === 4 ? Math.floor(count / 3) * inst : 0;
    T.draws += 1; T.tris += tris;
    if (T.fb) { T.fbDraws += 1; T.fbTris += tris; }
    const k = T.fb ? fbId.get(T.fb) : 0;
    const e = T.perFb.get(k) ?? { draws: 0, tris: 0 }; e.draws += 1; e.tris += tris; T.perFb.set(k, e);
  };
  for (const C of [WebGL2RenderingContext]) {
    const p = C.prototype;
    const de = p.drawElements; p.drawElements = function (m, c, t, o) { note(c, 1, m); return de.call(this, m, c, t, o); };
    const da = p.drawArrays; p.drawArrays = function (m, f, c) { note(c, 1, m); return da.call(this, m, f, c); };
    const dei = p.drawElementsInstanced; p.drawElementsInstanced = function (m, c, t, o, i) { note(c, i, m); return dei.call(this, m, c, t, o, i); };
    const dai = p.drawArraysInstanced; p.drawArraysInstanced = function (m, f, c, i) { note(c, i, m); return dai.call(this, m, f, c, i); };
    const dre = p.drawRangeElements; p.drawRangeElements = function (m, s, e, c, t, o) { note(c, 1, m); return dre.call(this, m, s, e, c, t, o); };
    const bf = p.bindFramebuffer; p.bindFramebuffer = function (tg, fb) {
      if (tg === this.FRAMEBUFFER || tg === this.DRAW_FRAMEBUFFER) { T.fb = fb; T.binds += 1; if (fb && !fbId.has(fb)) fbId.set(fb, nextFb++); }
      return bf.call(this, tg, fb);
    };
    const cl = p.clear; p.clear = function (b) { T.clears += 1; return cl.call(this, b); };
    const ge = p.getExtension; p.getExtension = function (name) {
      const ext = ge.call(this, name);
      if (ext && name === 'WEBGL_multi_draw' && !ext.__w) {
        ext.__w = true;
        const mde = ext.multiDrawElementsWEBGL.bind(ext);
        ext.multiDrawElementsWEBGL = function (m, counts, co, t, offs, oo, n) {
          for (let i = 0; i < n; i += 1) note(counts[co + i], 1, m);
          return mde(m, counts, co, t, offs, oo, n);
        };
        if (ext.multiDrawElementsInstancedWEBGL) {
          const mdei = ext.multiDrawElementsInstancedWEBGL.bind(ext);
          ext.multiDrawElementsInstancedWEBGL = function (m, counts, co, t, offs, oo, inst, io, n) {
            for (let i = 0; i < n; i += 1) note(counts[co + i], inst[io + i], m);
            return mdei(m, counts, co, t, offs, oo, inst, io, n);
          };
        }
      }
      return ext;
    };
  }
}

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'] });
const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1, isMobile: true, hasTouch: true });
await ctx.addInitScript(glTally);
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
page.on('console', (m) => { if (m.text().startsWith('[pose]')) console.log(m.text()); if (m.type() === 'error') errors.push(`console: ${m.text()}`.slice(0, 300)); });
const t0 = Date.now();
await page.goto(`http://127.0.0.1:${PORT}/${YEAR}/${QS ? `?${QS}` : ''}`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 420_000 });
await page.evaluate(async () => {
  const w = window.__chicago4d.welcome; const deadline = Date.now() + 90_000;
  while (w && w.state !== 'world' && Date.now() < deadline) {
    if (w.state === 'welcome') w.enter('spawn');
    if (w.state !== 'world') await new Promise((r) => setTimeout(r, 100));
  }
});
console.log(`booted ${YEAR} in ${((Date.now() - t0) / 1000).toFixed(0)} s`);

const out = await page.evaluate(async ({ tier, pose, ts, layers, brk }) => {
  const a = window.__chicago4d;
  const { SCENE_POSES, poseFrom } = await import('/walk/js/pacing-read.js');
  const poses = SCENE_POSES[String(a.scene?.id ?? a.year ?? '')];
  if (a.detail !== tier) await a.setDetail(tier);
  a.setGovernor(false);
  a.setAnimationHold(true);
  const raf = () => new Promise((r) => requestAnimationFrame(r));
  const gl = a.renderer.getContext();
  const T = window.__glT;
  const snap = () => ({ draws: T.draws, tris: T.tris, fbDraws: T.fbDraws, fbTris: T.fbTris, clears: T.clears, binds: T.binds });
  const sub = (x, y) => Object.fromEntries(Object.keys(x).map((k) => [k, x[k] - y[k]]));
  // One whole frame, driven: the page's own tick (`step`), GL tallied, wall time with a finish.
  const frame = () => {
    const px0 = new Uint8Array(4); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px0);
    const s0 = snap(); T.perFb = new Map();
    const t0 = performance.now();
    a.step();
    const t1 = performance.now();
    const px = new Uint8Array(4); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
    const t2 = performance.now();
    const info = a.renderer.info.render;
    // T-2970: the page's own driver-draw meter (driver-draws.js), the figure the draw
    // budgets read, beside the GL's count of the same frame — it is right when they agree.
    return { gl: sub(snap(), s0), perFb: [...T.perFb.entries()], info: { calls: info.calls, tris: info.triangles },
      page: a.stats().drawCalls,
      stepMs: t1 - t0, finishMs: t2 - t1 };
  };
  const settleFrames = async (n = 3) => { let f; for (let i = 0; i < n; i += 1) f = frame(); return f; };
  const groups = () => a.scene3d.children.filter((o) => o.name).map((o) => o.name);
  const fn = poseFrom(poses, pose);
  const results = [];
  for (const t of ts) {
    const p = fn(t);
    a.setFly(pose === 'flight');
    a.walker.teleport(p);
    // let reach/residency/LOD settle at the pose
    for (let i = 0; i < 3; i += 1) { frame(); await raf(); }
    for (let i = 0; i < 40 && (a.residency?.pending ?? 0) > 0; i += 1) { frame(); await raf(); }
    const base = await settleFrames(2); console.log(`[pose] base ${base.gl.draws} draws finish ${base.finishMs.toFixed(0)} ms`);
    const cam = a.camera.position;
    const rig = a.world.shadowRig;
    const res = { t, pose: p, cam: [cam.x, cam.y, cam.z].map((v) => +v.toFixed(1)), ratio: a.renderer.getPixelRatio(),
      size: [a.renderer.domElement.width, a.renderer.domElement.height],
      shadow: { reach: rig.reachM, map: rig.mapSize, enabled: a.renderer.shadowMap.enabled, autoUpdate: a.renderer.shadowMap.autoUpdate },
      coalesce: a.buildings?.coalesce ? { ...a.buildings.coalesce } : null, base, rows: [] };
    res.breakdown = {};
    for (const gname of brk) {
      const g = a.scene3d.getObjectByName(gname); if (!g) continue;
      frame();
      const rows = [];
      g.traverse((o) => {
        if (!o.isMesh) return;
        let vis = o.visible; for (let p = o.parent; p; p = p.parent) if (!p.visible) vis = false;
        if (!vis) return;
        const geo = o.geometry; const per = geo?.index ? geo.index.count : (geo?.attributes?.position?.count ?? 0);
        let tris = 0, draws = 1;
        if (o.isBatchedMesh) { draws = o._multiDrawCount; for (let i = 0; i < o._multiDrawCount; i++) tris += o._multiDrawCounts[i]; tris = Math.floor(tris / 3); }
        else if (o.isInstancedMesh) tris = Math.floor(per / 3) * o.count;
        else tris = Math.floor(per / 3);
        const m = [].concat(o.material)[0];
        rows.push({ name: o.name || o.parent?.name || '?', type: o.isBatchedMesh ? 'batched' : o.isInstancedMesh ? 'inst' : 'mesh', draws, tris,
          transparent: !!m?.transparent, alphaTest: m?.alphaTest || 0, cast: o.castShadow, mapW: m?.map?.image?.width ?? null });
      });
      rows.sort((p, q) => q.tris - p.tris);
      res.breakdown[gname] = rows.slice(0, 25);
    }
    // the sun, whole
    a.renderer.shadowMap.enabled = false; const noSun = await settleFrames(2); // the first frame after the switch recompiles
    a.renderer.shadowMap.enabled = true; await settleFrames(1);
    res.sun = { draws: base.gl.draws - noSun.gl.draws, tris: base.gl.tris - noSun.gl.tris,
      finishMs: +(base.finishMs - noSun.finishMs).toFixed(1) };
    if (layers) for (const name of groups()) {
      const g = a.scene3d.getObjectByName(name);
      if (!g || !g.visible) { res.rows.push({ name, hiddenAlready: true }); continue; }
      let meshes = 0, casters = 0, transparent = 0, alphaTest = 0, held = 0, visibleMeshes = 0;
      g.traverse((o) => {
        if (!o.isMesh) return; meshes += 1; if (o.visible) visibleMeshes += 1; if (o.castShadow) casters += 1;
        for (const m of [].concat(o.material)) { if (m?.transparent) transparent += 1; if (m?.alphaTest > 0 || m?.alphaHash) alphaTest += 1; }
        const geo = o.geometry; const n = geo?.index ? geo.index.count : (geo?.attributes?.position?.count ?? 0);
        held += Math.floor(n / 3) * (o.isInstancedMesh ? o.count : 1);
      });
      console.log(`[pose] layer ${name}`); g.visible = false; const hid = await settleFrames(1); g.visible = true;
      const restore = []; g.traverse((o) => { if (o.isMesh && o.castShadow) { restore.push(o); o.castShadow = false; } });
      let ns = null;
      if (restore.length) { ns = await settleFrames(1); for (const o of restore) o.castShadow = true; }
      res.rows.push({ name, meshes, visibleMeshes, casters, transparent, alphaTest, held,
        draws: base.gl.draws - hid.gl.draws, tris: base.gl.tris - hid.gl.tris,
        finishMs: +(base.finishMs - hid.finishMs).toFixed(1), stepMs: +(base.stepMs - hid.stepMs).toFixed(1),
        sunDraws: ns ? base.gl.draws - ns.gl.draws : 0, sunTris: ns ? base.gl.tris - ns.gl.tris : 0 });
    }
    const again = await settleFrames(1);
    res.again = again;
    results.push(res);
  }
  a.setAnimationHold(false);
  return { scene: String(a.scene?.id ?? a.year), detail: a.detail, results };
}, { tier: TIER, pose: POSE, ts: TS, layers: LAYERS, brk: BREAK });

const num = (n) => (n ?? 0).toLocaleString('en-US');
console.log(`scene ${out.scene} detail ${out.detail} pose ${POSE} viewport ${W}x${H}`);
for (const r of out.results) {
  console.log(`\nt=${r.t}s pose ${JSON.stringify(r.pose)} cam ${r.cam} ratio ${r.ratio} canvas ${r.size} shadow ${JSON.stringify(r.shadow)}`);
  console.log(`  frame: gl draws ${r.base.gl.draws} tris ${num(r.base.gl.tris)} (to FBOs ${r.base.gl.fbDraws}/${num(r.base.gl.fbTris)}) clears ${r.base.gl.clears} binds ${r.base.gl.binds}; three info calls ${r.base.info.calls} tris ${num(r.base.info.tris)}; page meter ${r.base.page} draws (${r.base.page === r.base.gl.draws ? 'agrees with the GL' : `GL ${r.base.gl.draws - r.base.page > 0 ? '+' : ''}${r.base.gl.draws - r.base.page}`}); step ${r.base.stepMs.toFixed(1)} ms finish ${r.base.finishMs.toFixed(1)} ms`);
  console.log(`  coalesce ${JSON.stringify(r.coalesce)}`);
  console.log(`  per framebuffer: ${JSON.stringify(r.base.perFb)}`);
  console.log(`  sun: ${r.sun.draws} draws ${num(r.sun.tris)} tris finish ${r.sun.finishMs} ms`);
  console.log('  layer               draws        tris   sunDraws     sunTris  finishMs  stepMs  meshes vis casters transp alphaT       held');
  for (const x of r.rows.slice().sort((p, q) => (q.tris ?? 0) - (p.tris ?? 0))) {
    if (x.hiddenAlready) { console.log(`  ${x.name.padEnd(18)} (hidden)`); continue; }
    console.log(`  ${x.name.padEnd(18)} ${String(x.draws).padStart(6)} ${num(x.tris).padStart(11)} ${String(x.sunDraws).padStart(9)} ${num(x.sunTris).padStart(11)} ${String(x.finishMs).padStart(9)} ${String(x.stepMs).padStart(7)} ${String(x.meshes).padStart(7)} ${String(x.visibleMeshes).padStart(3)} ${String(x.casters).padStart(7)} ${String(x.transparent).padStart(6)} ${String(x.alphaTest).padStart(6)} ${num(x.held).padStart(10)}`);
  }
  for (const [g, rows] of Object.entries(r.breakdown ?? {})) {
    console.log(`  breakdown ${g}:`);
    for (const x of rows) console.log(`    ${String(x.name).slice(0, 40).padEnd(40)} ${x.type.padEnd(7)} draws ${String(x.draws).padStart(5)} tris ${num(x.tris).padStart(9)} ${x.transparent ? 'blend' : ''} ${x.alphaTest ? 'aT' : ''} ${x.cast ? 'cast' : ''} map ${x.mapW}`);
  }
  console.log(`  again: draws ${r.again.gl.draws} tris ${num(r.again.gl.tris)} finish ${r.again.finishMs.toFixed(1)} ms`);
}
if (errors.length) console.log(`\nERRORS: ${errors.slice(0, 8).join('\n')}`);
if (jsonOut) fs.writeFileSync(jsonOut, JSON.stringify(out, null, 2));
await browser.close(); server.close();
