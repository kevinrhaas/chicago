/**
 * WHAT A STILL FRAME COSTS, STAND BY STAND, AND WHOSE MILLISECONDS THEY ARE (T-2099).
 *
 *   node tools/measure_still_frame.mjs [--source] [--year 1835|1812|1904]
 *        [--only desktop|mobile|both] [--tiers full,balanced,light]
 *        [--stands a,b] [--sharpness 1,1.5,2] [--attribute | --attribute-at id]
 *        [--frames N] [--warmup N] [--throttle N] [--json out.json]
 *        [--arrival [seconds]] [--jaunt id]
 *   node tools/measure_still_frame.mjs --gate [--only desktop|mobile]
 *
 * The owner, 2026-10-04: "that lag is all over not just walking". T-2096 owns the
 * cost of MOVING (rebuilds fired by a walk, a turn, a flight). This reads the
 * other half: the cost of a frame in which nothing is rebuilt at all — standing
 * at a stand, the aerial, another year's landing view. Until now the project had
 * read a still frame's GEOMETRY at every stand (`measure_detail_ceilings.mjs`,
 * `measure_layer_share.mjs`) and its TIME at exactly one, in the wet woods
 * (`measure_shrub_frame_cost.mjs`). Triangles are not milliseconds: a soft
 * shadow filter, a per-fragment ground shader and the pixel ratio cost time and
 * show in no triangle count.
 *
 * THE METHOD IS `measure_shrub_frame_cost.mjs`'s, unchanged, for the reasons
 * written there: the clock is held (`setAnimationHold`) so the wind does not
 * blow between two frames meant to differ in one thing; the loop is stopped and
 * frames are driven by `step()`, so the browser's display pacing is not what is
 * measured; and every frame ends in a one-pixel `readPixels`, the only real fence
 * on a renderer whose rasteriser runs in another process. Two clocks per frame:
 *
 *   cpu ..... `step()` alone — the walk of the scene, the uniforms and the
 *             submission of every draw call: the side a draw-call count prices.
 *   frame ... `step()` and the fence — the frame actually drawn. frame − cpu is
 *             the raster's share: fill, the shadow pass, the fragment shaders.
 *
 * `--attribute` draws each named layer of the scene ALONE and prints what it
 * costs over a frame with every layer hidden; then each PASS that is not a layer
 * — the shadow map's own render (`shadowMap.autoUpdate`), the soft filter
 * (PCFSoft over PCF) and glass's transmission pass — priced against the whole
 * frame. Alone rather than by
 * subtraction because a whole frame on this runner is SECONDS (7.4 s at the
 * landing, 11.1 s at the forks, `full`, 1280x800, measured 2026-10-04), and a
 * subtraction per layer is a whole frame per layer.
 *
 * WHAT THE FIGURES ARE AND ARE NOT. Headless Chromium on this project's runners
 * draws through SwiftShader, a software rasteriser; the device string is printed
 * on every reading so none is quoted without it. The absolute milliseconds are
 * this machine's, not a phone's. The SHARES are the point: a software rasteriser
 * is the most fill-sensitive witness there is, so a pass that is cheap here is
 * cheap on a GPU, and one that dominates here is the first suspect there.
 *
 * The phone stand-in is 390x780 at a device pixel ratio of 3 (an iPhone's),
 * touch, so the renderer boots the way it does on the owner's phone — coarse
 * pointer, low-spec shadows, Image sharpness Medium = 1.5 — with the CPU
 * throttled `--throttle` times (default 4) through the DevTools protocol.
 *
 * THE ARRIVAL SCREEN AND A JAUNT VIEW (T-2111). The arrival and the welcome are
 * a menu laid over the town, and the town under them is the landing view: the
 * `landing` row IS the arrival screen's frame, read with the gate up (the
 * renderer holds the walk while it is). What the landing row cannot say is how
 * OFTEN that frame is drawn, so `--arrival [s]` (default 15) leaves the loop
 * running for that long before anything is timed and counts the frames drawn
 * and whether the picture changed between the first and the last of them. A
 * jaunt view is read at the `jaunt` stand: the outing is started for real
 * (`--jaunt id`, default the year's featured one) and timed at its first stop,
 * with its panel up; later tiers return to the pose it stood at.
 *
 * `--gate` HOLDS THE CEILING (T-2111): a still-frame time ceiling per tier at
 * the worst stand, beside T-1975's triangle ceilings (`DETAIL` in `main.js`),
 * written down in `tools/still_frame_ceilings.json` with the reading it was set
 * on. A millisecond on a software rasteriser is the MACHINE's, so the ceilings
 * are kept per machine (CPU model and core count, printed on every reading) and
 * a machine with no ceilings of its own is read and warned about, never failed
 * on another machine's numbers; `--strict` fails it. The frame is also printed
 * in BARE SCREENS (over a frame with every layer hidden, timed in the same
 * page), which was the first design for a machine-free unit and is NOT gated:
 * the two machines read on 2026-10-04 moved the frame and the bare screen in
 * opposite directions, so the ratio differed by a quarter where the
 * milliseconds differed by a tenth. `.github/workflows/chicago-4d-frame-time.yml`
 * runs the gate.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

async function loadPlaywright() {
  let ns;
  try {
    ns = await import('playwright');
  } catch {
    const root = (process.env.NODE_PATH
      || execSync('npm root -g', { encoding: 'utf8' })).trim().split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT4D = path.resolve(HERE, '..');
const argAt = (name) => {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : null;
};
const list = (name, dflt) => (argAt(name) || dflt).split(',').filter(Boolean);
const wantSource = process.argv.includes('--source');
const attribute = process.argv.includes('--attribute');
// `--attribute-at id` attributes at that one stand and only times the rest.
const attributeAt = argAt('--attribute-at');
const jsonOut = argAt('--json');
const ONLY = argAt('--only') || 'both';
// THE GATE TAKES ITS YEAR, STAND AND TIERS FROM THE CEILINGS FILE, so what is
// held is what was written down and not whatever the command line said.
const GATE = process.argv.includes('--gate');
const CEILINGS_PATH = path.join(path.dirname(fileURLToPath(import.meta.url)), 'still_frame_ceilings.json');
const CEILINGS = GATE ? JSON.parse(fs.readFileSync(CEILINGS_PATH, 'utf8')) : null;
const YEAR = CEILINGS?.year || argAt('--year') || '1835';
const TIERS = CEILINGS ? Object.keys(CEILINGS.tiers) : list('--tiers', 'full,balanced,light');
const FRAMES = Number(argAt('--frames') || 2);
const WARMUP = Number(argAt('--warmup') || 0);
const THROTTLE = Number(argAt('--throttle') || 4);
const SHARPNESS = argAt('--sharpness') ? list('--sharpness', '').map(Number) : null;
// `--arrival` alone is 15 s; a number after it is the window.
const ARRIVAL = process.argv.includes('--arrival')
  ? (Number(argAt('--arrival')) > 0 ? Number(argAt('--arrival')) : 15) : 0;
// The outing a jaunt view is read in: the year's featured one, its first stop.
const JAUNT = argAt('--jaunt')
  || ({ 1835: 'fort-dearborn-errand', 1904: 'prairie-avenue-orientation' })[YEAR] || null;

// THE STANDS ARE `measure_detail_ceilings.mjs`'s, COPIED for the reason it copies
// them from the smoke: the gate's six downtown stands (T-0135's five and T-2015's
// prairie) and T-2084's three in-town poses, which T-2092 reads the new ground at —
// so a millisecond here sits beside a triangle there, stand for stand. They are
// 1835's. Another year is read at the stand it lands a visitor on (`landing`).
const STANDS_1835 = [
  { id: 'sauganash_26', kind: 'frame', target: 'sauganash_hotel', distance: 26 },
  { id: 'lake_at_canal', kind: 'anchor', target: 'lake_at_canal' },
  { id: 'the_forks', kind: 'anchor', target: 'forks' },
  { id: 'lake_and_market', kind: 'anchor', target: 'lake_market' },
  { id: 'prairie_west', kind: 'pose',
    pose: { local_e: -250, local_n: -150, yaw_deg: 90, pitch_deg: -8 } },
  { id: 'town_backyard', kind: 'pose',
    pose: { local_e: 385, local_n: -450, yaw_deg: 0, pitch_deg: -6 } },
  { id: 'town_lake_shoulder', kind: 'pose',
    pose: { local_e: 520, local_n: -104, yaw_deg: 270, pitch_deg: -6 } },
  { id: 'town_south_water_store', kind: 'pose',
    pose: { local_e: 501, local_n: -2, yaw_deg: 180, pitch_deg: -6 } },
  { id: 'from_above', kind: 'anchor', target: 'from_above', aerial: true },
];
const LANDING = [{ id: 'landing', kind: 'landing' }];
// LAST, because starting an outing closes the welcome: every stand before it is
// read with the gate up, as a visitor first sees the town.
const JAUNT_STAND = JAUNT ? [{ id: 'jaunt', kind: 'jaunt', jaunt: JAUNT }] : [];
const standFilter = CEILINGS ? [CEILINGS.stand]
  : argAt('--stands')?.split(',').filter(Boolean) ?? null;
const STANDS = [...LANDING, ...(YEAR === '1835' ? STANDS_1835 : []), ...JAUNT_STAND]
  .filter((st) => !standFilter || standFilter.includes(st.id));

const VIEWPORTS = [
  { label: 'desktop 1280x800', width: 1280, height: 800, dsf: 1, mobile: false },
  { label: `phone 390x780 dpr3 cpu/${THROTTLE}`, width: 390, height: 780, dsf: 3, mobile: true },
].filter((v) => ONLY === 'both' || (ONLY === 'mobile' ? v.mobile : !v.mobile));

const root = wantSource
  ? path.join(ROOT4D, 'renderers/web')
  : path.resolve(ROOT4D, '../../site/4d');
const entry = wantSource ? '/index.html' : '/walk/index.html';
if (!fs.existsSync(root)) {
  console.error(`no tree at ${root}${wantSource ? '' : ' — run tools/publish.sh first'}`);
  process.exit(2);
}

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.webp': 'image/webp', '.svg': 'image/svg+xml', '.wasm': 'application/wasm',
  '.md': 'text/markdown',
};
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(root, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(root) || !fs.existsSync(file)) {
    res.writeHead(404, { 'content-type': 'text/plain' });
    res.end(`not found: ${url}`);
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const PORT = server.address().port;

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
});
const passes = [];
for (const vp of VIEWPORTS) {
  const ctx = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    deviceScaleFactor: vp.dsf, isMobile: vp.mobile, hasTouch: vp.mobile,
  });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (m) => { if (m.text().startsWith('still-frame ')) console.log(m.text()); });
  await page.goto(`http://127.0.0.1:${PORT}${entry}?year=${YEAR}`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 300_000 });
  // Throttle AFTER the boot: the boot is not what this reads, and a four-times
  // slower boot on a software rasteriser spends the run before a frame is timed.
  if (vp.mobile && THROTTLE > 1) {
    const cdp = await ctx.newCDPSession(page);
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: THROTTLE });
  }
  const seen = await page.evaluate(async ({ stands, tiers, frames, warmup, sharpness,
    attribute, attributeAt, label, arrival, gate }) => {
    const a = window.__chicago4d;
    const r = a.renderer;
    // THE ARRIVAL SCREEN, read while the page is as a visitor first sees it: the
    // loop running, the welcome up, nothing touched. How many frames the renderer
    // draws in the window, and whether the last of them is the picture the first
    // one was (the signature `capture()` reads back inside the frame it drew).
    let arrivalRead = null;
    if (arrival > 0) {
      const sigA = await a.capture(12);
      const f0 = r.info.render.frame; const t0 = performance.now();
      await new Promise((res) => setTimeout(res, arrival * 1000));
      const f1 = r.info.render.frame; const t1 = performance.now();
      const sigB = await a.capture(12);
      const same = JSON.stringify(sigA) === JSON.stringify(sigB);
      arrivalRead = { welcome: a.welcome?.state ?? null,
        gateUp: !document.getElementById('gate')?.hidden,
        seconds: Math.round((t1 - t0) / 100) / 10, framesDrawn: f1 - f0,
        perSecond: Math.round(((f1 - f0) / ((t1 - t0) / 1000)) * 100) / 100,
        pictureUnchanged: same };
      console.log(`still-frame ${label} arrival ${JSON.stringify(arrivalRead)}`);
    }
    r.setAnimationLoop(null);
    a.setAnimationHold(true);
    const gl = r.getContext();
    const dbg = gl.getExtension('WEBGL_debug_renderer_info');
    const device = String(dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL)
      : gl.getParameter(gl.RENDERER));
    const timerQuery = !!gl.getExtension('EXT_disjoint_timer_query_webgl2');
    const px = new Uint8Array(4);
    const fenced = () => { gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); };
    let jaunt = null;
    const settle = () => { for (let i = 0; i < 2; i++) { a.step(); fenced(); } };
    // One reading: `warmup` frames thrown away (a program compiled, a shadow map
    // allocated), then `frames` timed. Medians, because one GC pause in six
    // frames is the browser's, not the scene's.
    const time = () => {
      for (let i = 0; i < warmup; i++) { a.step(); fenced(); }
      const cpu = []; const frame = [];
      for (let i = 0; i < frames; i++) {
        const t0 = performance.now();
        a.step();
        const t1 = performance.now();
        fenced();
        const t2 = performance.now();
        cpu.push(t1 - t0); frame.push(t2 - t0);
      }
      const med = (xs) => { const s = [...xs].sort((x, y) => x - y); return s[s.length >> 1]; };
      const st = a.stats();
      return { frame: med(frame), cpu: med(cpu), worst: Math.max(...frame),
               triangles: st.triangles, calls: st.drawCalls };
    };
    const round = (o) => Object.fromEntries(Object.entries(o)
      .map(([k, v]) => [k, typeof v === 'number' ? Math.round(v * 10) / 10 : v]));
    const landing = { ...a.walker.state };
    // A JAUNT VIEW: the outing started for real and stepped to its first stop.
    // The loop is stopped, so the ride is driven here — `travel.simulate` for the
    // walk to the stop, a frame at a time otherwise, and both bounded. The pose
    // it stood at is kept, so the next tier is read from exactly there.
    let jauntPose = null;
    const place = async (st) => {
      if (st.kind === 'jaunt') {
        if (jauntPose) { a.walker.teleport(jauntPose); return; }
        if (!(await a.jaunts.start(st.jaunt))) throw new Error(`jaunt ${st.jaunt} did not start`);
        for (let i = 0; i < 40 && a.jaunts.state?.phase !== 'atStop'; i++) {
          if (a.travel.state.phase !== 'idle') a.travel.simulate(600);
          a.step(); fenced();
          await new Promise((res) => setTimeout(res, 100));
        }
        const js = a.jaunts.state;
        if (js?.phase !== 'atStop') throw new Error(`jaunt ${st.jaunt} stuck in ${js?.phase}`);
        jauntPose = { local_e: a.walker.state.e, local_n: a.walker.state.n,
          yaw_deg: a.player.bearingDeg, pitch_deg: a.player.pitchDeg,
          ...(a.player.flying ? { altitude_m: a.player.altitude } : {}) };
        jaunt = { id: js.jaunt?.id, stop: js.stopIndex, ...jauntPose };
        return;
      }
      if (st.kind === 'landing') {
        a.setFly(false);
        a.walker.teleport({ local_e: landing.e, local_n: landing.n,
          yaw_deg: a.player.bearingDeg ?? 0 });
      } else if (st.kind === 'frame') { a.setFly(false); a.frame(st.target, st.distance); }
      else if (st.kind === 'pose') {
        a.setFly(typeof st.pose.altitude_m === 'number');
        a.walker.teleport(st.pose);
      } else a.goTo(st.target);
    };
    // The PASSES a layer toggle cannot reach. Each returns its own undo.
    const shadowTypeWas = r.shadowMap.type;
    const remakeMaterials = () => a.scene3d.traverse((o) => {
      for (const m of [].concat(o.material || [])) m.needsUpdate = true;
    });
    const PASSES = {
      'shadow map render': () => {
        r.shadowMap.autoUpdate = false; r.shadowMap.needsUpdate = false;
        return () => { r.shadowMap.autoUpdate = true; r.shadowMap.needsUpdate = true; };
      },
      'soft shadow filter': () => {
        // PCFSoft (2) is what a desktop with a GPU boots with, PCF (1) a low-spec
        // one; whichever this boot has, the other is drawn, and the cost printed is
        // always PCFSoft's over PCF's.
        if (shadowTypeWas !== 1 && shadowTypeWas !== 2) return null;
        r.shadowMap.type = 3 - shadowTypeWas; remakeMaterials();
        return () => { r.shadowMap.type = shadowTypeWas; remakeMaterials(); };
      },
      // T-2099, 1904: glass carrying KHR_materials_transmission makes three draw
      // every opaque object a second time, into a target the glass then samples.
      // Priced by taking the transmission off; the pass exists only while some
      // visible material has it, so the frame without it is the frame without the pass.
      'transmission pass': () => {
        const glass = [];
        a.scene3d.traverse((o) => {
          for (const m of [].concat(o.material || [])) {
            if (m.transmission > 0) { glass.push([m, m.transmission]); m.transmission = 0; }
          }
        });
        if (!glass.length) return null;
        return () => { for (const [m, t] of glass) m.transmission = t; };
      },
    };
    const dpr = window.devicePixelRatio || 1;
    const ratioWas = r.getPixelRatio();
    const rows = [];
    for (const level of tiers) {
      await a.setDetail(level);
      settle();
      for (const st of stands) {
        await place(st);
        settle();
        for (const q of (sharpness || [null])) {
          if (q !== null) { r.setPixelRatio(Math.min(dpr, q)); settle(); }
          const whole = time();
          const row = { level, stand: st.id, sharpness: q, pixelRatio: r.getPixelRatio(),
                        ...round(whole) };
          if (attribute || st.id === attributeAt) {
            // EACH LAYER ALONE, against the frame with every layer hidden. A
            // subtraction from the whole frame (the triangle tools' method) costs a
            // whole frame per layer, and a whole frame here is seconds; drawn alone,
            // the layers together cost about one. What it gives up is overlap: a
            // layer drawn alone is not hidden behind another, so the parts sum to
            // more than the whole, and the printed `sum` says by how much.
            row.by = {};
            const layers = a.scene3d.children.filter((c) => c.name && c.name !== 'sky'
              && !c.isLight && c.visible);
            for (const layer of layers) layer.visible = false;
            settle();
            const empty = time();
            row.empty = round(empty);
            for (const layer of layers) {
              layer.visible = true;
              settle();
              const alone = time();
              layer.visible = false;
              row.by[layer.name] = round({ frame: alone.frame - empty.frame,
                cpu: alone.cpu - empty.cpu, triangles: alone.triangles - empty.triangles,
                calls: alone.calls - empty.calls });
            }
            for (const layer of layers) layer.visible = true;
            settle();
            row.sum = Math.round(Object.values(row.by).reduce((t, v) => t + v.frame, 0)
              + empty.frame);
            // The PASSES, priced against the whole frame: a pass is not a layer.
            for (const [name, toggle] of Object.entries(PASSES)) {
              const undo = toggle();
              if (!undo) continue;
              settle();
              const other = time();
              undo();
              settle();
              row.by[`(${name})`] = round({ frame: name.startsWith('soft')
                ? (shadowTypeWas === 2 ? whole.frame - other.frame : other.frame - whole.frame)
                : whole.frame - other.frame, cpu: whole.cpu - other.cpu,
                triangles: whole.triangles - other.triangles, calls: whole.calls - other.calls });
            }
          }
          if (gate) {
            // THE BARE SCREEN this frame is gated in units of: every layer hidden,
            // timed in the same page at the same pixel ratio, more frames than the
            // whole because it is the denominator and a short one.
            const layers = a.scene3d.children.filter((c) => c.name && c.name !== 'sky'
              && !c.isLight && c.visible);
            for (const layer of layers) layer.visible = false;
            settle();
            const fr = frames; frames = 5;
            row.bare = round(time());
            frames = fr;
            for (const layer of layers) layer.visible = true;
            settle();
            row.screens = Math.round((row.frame / row.bare.frame) * 10) / 10;
          }
          console.log(`still-frame ${label} ${JSON.stringify(row)}`);
          rows.push(row);
          if (q !== null) { r.setPixelRatio(ratioWas); }
        }
      }
    }
    return { device, timerQuery, dpr, lowSpecShadows: shadowTypeWas !== 2, arrival: arrivalRead,
             jaunt, rows };
  }, { stands: STANDS, tiers: TIERS, frames: FRAMES, warmup: WARMUP, sharpness: SHARPNESS,
       attribute, attributeAt, label: vp.label, arrival: ARRIVAL, gate: GATE });
  passes.push({ viewport: vp.label, ...seen, errors });
  await ctx.close();
}
await browser.close();
server.close();

let bad = 0;
for (const pass of passes) {
  console.log(`\n================  ${pass.viewport}  ·  ${YEAR}  ================`);
  console.log(`device: ${pass.device} · timer query: ${pass.timerQuery ? 'yes' : 'no'} · `
    + `dpr ${pass.dpr} · shadows ${pass.lowSpecShadows ? 'PCF (low-spec)' : 'PCFSoft'}`);
  for (const e of pass.errors) { bad++; console.log(`  PAGEERROR  ${e}`); }
  if (pass.arrival) {
    const ar = pass.arrival;
    console.log(`arrival screen (welcome ${ar.welcome}, gate ${ar.gateUp ? 'up' : 'down'}): `
      + `${ar.framesDrawn} frame(s) drawn in ${ar.seconds} s with nothing touched, `
      + `${ar.perSecond}/s; the picture ${ar.pictureUnchanged ? 'did NOT change' : 'changed'}`);
  }
  if (pass.jaunt) {
    console.log(`jaunt view: ${pass.jaunt.id}, stop ${pass.jaunt.stop + 1}, at `
      + `(${pass.jaunt.local_e.toFixed(1)}, ${pass.jaunt.local_n.toFixed(1)}) facing `
      + `${pass.jaunt.yaw_deg.toFixed(0)}°`);
  }
  console.log(`${'tier'.padEnd(9)}${'stand'.padEnd(24)}${'px'.padStart(5)}`
    + `${'frame ms'.padStart(10)}${'cpu ms'.padStart(9)}${'worst'.padStart(8)}`
    + `${'triangles'.padStart(12)}${'calls'.padStart(7)}`);
  for (const row of pass.rows) {
    console.log(`${row.level.padEnd(9)}${row.stand.padEnd(24)}${String(row.pixelRatio).padStart(5)}`
      + `${row.frame.toFixed(1).padStart(10)}${row.cpu.toFixed(1).padStart(9)}`
      + `${row.worst.toFixed(1).padStart(8)}${row.triangles.toLocaleString().padStart(12)}`
      + `${String(row.calls).padStart(7)}`
      + (row.bare ? `   bare screen ${row.bare.frame.toFixed(1)} ms → ${row.screens} screens` : ''));
    if (row.empty) {
      console.log(`${''.padEnd(13)}${'(nothing drawn)'.padEnd(22)}${row.empty.frame.toFixed(1).padStart(8)} ms`
        + `   the parts alone sum to ${row.sum} ms against the whole frame's ${row.frame.toFixed(0)}`);
    }
    for (const [name, s] of Object.entries(row.by || {}).sort((x, y) => y[1].frame - x[1].frame)) {
      console.log(`${''.padEnd(13)}${name.padEnd(22)}${s.frame.toFixed(1).padStart(8)} ms`
        + `  ${(100 * s.frame / row.frame).toFixed(0).padStart(4)}%`
        + `${s.cpu.toFixed(1).padStart(8)} cpu${s.triangles.toLocaleString().padStart(12)}`
        + `${String(s.calls).padStart(6)}`);
    }
  }
}
// THE CEILING (T-2111). Each tier's frame at the worst stand, in milliseconds,
// against the number written in `still_frame_ceilings.json` for THIS machine and
// viewport. A machine the file does not know is read and warned about — its
// milliseconds are not another machine's — and fails only under `--strict`. On
// a known machine, a tier or viewport with no number is a failure, not a pass.
const CPU = { model: os.cpus()[0]?.model?.trim() || 'unknown', cores: os.cpus().length };
console.log(`\nmachine: ${CPU.model}, ${CPU.cores} core(s)`);
if (GATE) {
  const machine = CEILINGS.machines.find((m) => m.cpu === CPU.model && m.cores === CPU.cores);
  console.log(`\n================  the still-frame ceiling (${path.basename(CEILINGS_PATH)})  ================`);
  console.log(`year ${YEAR}, stand ${CEILINGS.stand}; ceilings for `
    + (machine ? `${machine.cpu}, ${machine.cores} cores (${machine.where})` : 'THIS MACHINE: none'));
  for (const pass of passes) {
    const vp = pass.viewport.startsWith('phone') ? 'mobile' : 'desktop';
    for (const row of pass.rows) {
      const ceiling = machine?.tiers[row.level]?.[vp];
      const ok = typeof ceiling === 'number' && row.frame <= ceiling;
      if (machine && !ok) bad++;
      console.log(`  ${ok ? 'ok  ' : machine ? 'FAIL' : '--  '}  ${vp.padEnd(8)} ${row.level.padEnd(9)} `
        + `${row.frame.toFixed(0).padStart(7)} ms  (ceiling ${ceiling ?? 'NONE'})`
        + `   ${row.screens} bare screens of ${row.bare.frame.toFixed(1)} ms, `
        + `${row.triangles.toLocaleString()} triangles`);
    }
  }
  if (!machine) {
    console.log(`::warning title=still-frame ceiling::no ceilings for ${CPU.model} (${CPU.cores} cores) `
      + `in ${path.basename(CEILINGS_PATH)}: read, not held. Add this machine's reading by the file's rule.`);
    if (process.argv.includes('--strict')) bad++;
  }
  console.log(bad ? `\nTHE CEILING IS BROKEN: ${bad} reading(s) over or unbudgeted. A parcel that `
    + 'makes every frame slower argues its own number in still_frame_ceilings.json, '
    + 'with the reading, in the same commit.' : machine ? '\nevery tier under its ceiling' : '');
}
if (jsonOut) {
  fs.writeFileSync(jsonOut, `${JSON.stringify({ ticket: GATE || ARRIVAL || JAUNT_STAND.length ? 'T-2111' : 'T-2099',
    tree: wantSource ? 'source' : 'published', year: YEAR, frames: FRAMES, warmup: WARMUP,
    throttle: THROTTLE, machine: CPU, passes }, null, 2)}\n`);
  console.log(`\nwritten ${jsonOut}`);
}
process.exit(bad ? 1 : 0);
