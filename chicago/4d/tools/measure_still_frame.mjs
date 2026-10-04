/**
 * WHAT A STILL FRAME COSTS, STAND BY STAND, AND WHOSE MILLISECONDS THEY ARE (T-2099).
 *
 *   node tools/measure_still_frame.mjs [--source] [--year 1835|1812|1904]
 *        [--only desktop|mobile|both] [--tiers full,balanced,light]
 *        [--stands a,b] [--sharpness 1,1.5,2] [--attribute | --attribute-at id]
 *        [--probe] [--capture dir]
 *        [--frames N] [--warmup N] [--throttle N] [--json out.json]
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
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
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
// `--probe` (T-2110): trees and the ground, each drawn alone as shipped and then
// with a cheaper material swapped in — see PROBES in the page below.
const probe = process.argv.includes('--probe');
// `--capture dir` writes each row's whole frame as a PNG, read in the same task
// as its draw — the picture a shader change must not move (T-2110).
const captureDir = argAt('--capture');
// `--attribute-at id` attributes at that one stand and only times the rest.
const attributeAt = argAt('--attribute-at');
const jsonOut = argAt('--json');
const ONLY = argAt('--only') || 'both';
const YEAR = argAt('--year') || '1835';
const TIERS = list('--tiers', 'full,balanced,light');
const FRAMES = Number(argAt('--frames') || 2);
const WARMUP = Number(argAt('--warmup') || 0);
const THROTTLE = Number(argAt('--throttle') || 4);
const SHARPNESS = argAt('--sharpness') ? list('--sharpness', '').map(Number) : null;

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
const standFilter = argAt('--stands')?.split(',').filter(Boolean) ?? null;
const STANDS = (YEAR === '1835' ? [...LANDING, ...STANDS_1835] : LANDING)
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
    attribute, attributeAt, probe, capture, label }) => {
    const a = window.__chicago4d;
    const r = a.renderer;
    r.setAnimationLoop(null);
    a.setAnimationHold(true);
    const gl = r.getContext();
    const dbg = gl.getExtension('WEBGL_debug_renderer_info');
    const device = String(dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL)
      : gl.getParameter(gl.RENDERER));
    const timerQuery = !!gl.getExtension('EXT_disjoint_timer_query_webgl2');
    const px = new Uint8Array(4);
    const fenced = () => { gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); };
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
    const place = (st) => {
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
    // T-2110's variants. `make(material)` returns the material to draw instead,
    // or null to leave that one alone; `swapIn` puts the shipped ones back.
    // The page's own three, through its import map: the same module instance the
    // scene was built with, so a swapped material is one the renderer knows.
    const THREE_ = probe ? await import('three').catch(() => null) : null;
    const swapIn = (layer, make) => {
      const undo = [];
      layer.traverse((o) => {
        if (!o.isMesh || !o.material || Array.isArray(o.material)) return;
        const next = make(o.material);
        if (!next) return;
        // A function is an in-place tweak's own undo; a material is a swap.
        if (typeof next === 'function') { undo.push([o, null, next]); return; }
        undo.push([o, o.material]);
        o.material = next;
      });
      if (!undo.length) return null;
      return () => {
        for (const [o, m, back] of undo) {
          if (back) { back(); continue; }
          if (m !== o.material) o.material.dispose?.();
          o.material = m;
        }
      };
    };
    const own = (m, patch) => { const c = m.clone(); patch(c); c.needsUpdate = true; return c; };
    const ground = (m) => !!m.userData?.groundTex;
    const PROBES = {
      trees: {
        // The bump reads the atlas three more times a fragment, and on a leaf
        // card the patch keeps 3.5 % of what it bends.
        'no bump': (m) => (m.bumpMap ? own(m, (c) => { c.bumpMap = null; }) : null),
        // Lambert: one diffuse term, no GGX, the same cut-out.
        'lambert, same cut-out': (m) => (m.isMeshStandardMaterial && THREE_
          ? new THREE_.MeshLambertMaterial({ map: m.map, alphaTest: m.alphaTest, side: m.side,
            vertexColors: m.vertexColors }) : null),
        // The floor: the same cards cut the same way, no light at all.
        'unlit, same cut-out': (m) => (m.isMeshStandardMaterial && THREE_
          ? new THREE_.MeshBasicMaterial({ map: m.map, alphaTest: m.alphaTest, side: m.side,
            vertexColors: m.vertexColors }) : null),
      },
      terrain: {
        // The turf chunk's eight value noises run only inside its mask's box; an
        // empty box (zero scale) is the ground with no turf anywhere.
        'no turf': (m) => {
          const box = ground(m) && r.properties.get(m)?.uniforms?.uTurfBox;
          if (!box) return null;
          const was = box.value.clone();
          box.value.set(0, 0, 0, 0);
          return () => box.value.copy(was);
        },
        // The same light model with none of the ground's own chunks: what the
        // prairie, sward, zone and turf GLSL cost on top of a lit plain.
        'lit, no ground chunks': (m) => (ground(m) && THREE_
          ? new THREE_.MeshStandardMaterial({ color: 0x7a8a4a, roughness: 1, metalness: 0 })
          : null),
        'unlit': (m) => (ground(m) && THREE_
          ? new THREE_.MeshBasicMaterial({ color: 0x7a8a4a }) : null),
      },
    };
    const dpr = window.devicePixelRatio || 1;
    const ratioWas = r.getPixelRatio();
    const rows = [];
    for (const level of tiers) {
      await a.setDetail(level);
      settle();
      for (const st of stands) {
        place(st);
        settle();
        for (const q of (sharpness || [null])) {
          if (q !== null) { r.setPixelRatio(Math.min(dpr, q)); settle(); }
          const whole = time();
          const row = { level, stand: st.id, sharpness: q, pixelRatio: r.getPixelRatio(),
                        ...round(whole) };
          if (capture) { a.step(); row.png = r.domElement.toDataURL('image/png'); }
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
          if (probe) {
            // T-2110. WHAT A CHEAPER SHADER COULD WIN, layer by layer: the layer
            // drawn alone as shipped, then with each variant swapped onto its
            // meshes. A variant is a ceiling on a saving, not a proposal — the
            // unlit ones draw a different picture on purpose, to price the
            // lighting and the custom chunks apart from the cover and the fill.
            row.probe = {};
            const layers = a.scene3d.children.filter((c) => c.name && c.name !== 'sky'
              && !c.isLight && c.visible);
            for (const layer of layers) layer.visible = false;
            settle();
            const empty = time();
            for (const [name, variants] of Object.entries(PROBES)) {
              const layer = layers.find((l) => l.name === name);
              if (!layer) continue;
              layer.visible = true;
              settle();
              const shipped = time();
              const out = { shipped: round({ frame: shipped.frame - empty.frame,
                triangles: shipped.triangles - empty.triangles }) };
              for (const [vname, make] of Object.entries(variants)) {
                const undo = swapIn(layer, make);
                if (!undo) continue;
                settle();
                const v = time();
                undo();
                out[vname] = round({ frame: v.frame - empty.frame,
                  triangles: v.triangles - empty.triangles,
                  saves: shipped.frame - v.frame });
              }
              settle();
              layer.visible = false;
              if (name === 'terrain') {
                // How many substrate zones the ground's fragment tests, each one
                // a ramped extent in the chunk `zoneGlsl` writes.
                layer.traverse((o) => { if (o.material?.userData?.substrateZones) {
                  out.zones = o.material.userData.substrateZones.length; } });
              }
              row.probe[name] = out;
            }
            for (const layer of layers) layer.visible = true;
            settle();
            // DRAWN LAST: the same frame with one layer sorted after every other
            // opaque thing, so a fragment something nearer already covers fails
            // the depth test instead of being shaded and painted over. Timed on
            // the WHOLE frame, and its pixels compared with the shipped frame's.
            const grab = () => {
              a.step();
              const w = gl.drawingBufferWidth; const h = gl.drawingBufferHeight;
              const b = new Uint8Array(w * h * 4);
              gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, b);
              return b;
            };
            const base = time();
            const basePx = grab();
            row.probe.order = { shipped: round({ frame: base.frame }) };
            for (const name of Object.keys(PROBES)) {
              const layer = layers.find((l) => l.name === name);
              if (!layer) continue;
              const was = layer.renderOrder;
              layer.renderOrder = 10;
              settle();
              const v = time();
              const px = grab();
              layer.renderOrder = was;
              let changed = 0; let most = 0;
              for (let i = 0; i < px.length; i += 4) {
                const d = Math.max(Math.abs(px[i] - basePx[i]), Math.abs(px[i + 1] - basePx[i + 1]),
                  Math.abs(px[i + 2] - basePx[i + 2]));
                if (d) { changed++; if (d > most) most = d; }
              }
              row.probe.order[`${name} last`] = round({ frame: v.frame, saves: base.frame - v.frame,
                pixelsChanged: changed / (px.length / 4), mostLevels: most });
            }
            settle();
          }
          console.log(`still-frame ${label} ${JSON.stringify({ ...row, png: undefined })}`);
          rows.push(row);
          if (q !== null) { r.setPixelRatio(ratioWas); }
        }
      }
    }
    return { device, timerQuery, dpr, lowSpecShadows: shadowTypeWas !== 2, rows };
  }, { stands: STANDS, tiers: TIERS, frames: FRAMES, warmup: WARMUP, sharpness: SHARPNESS,
       attribute, attributeAt, probe, capture: !!captureDir, label: vp.label });
  if (captureDir) {
    fs.mkdirSync(captureDir, { recursive: true });
    for (const row of seen.rows) {
      if (!row.png) continue;
      const name = `${vp.mobile ? 'phone' : 'desktop'}-${YEAR}-${row.level}-${row.stand}`
        + `${row.sharpness ? `-px${row.sharpness}` : ''}.png`;
      fs.writeFileSync(path.join(captureDir, name), Buffer.from(row.png.split(',')[1], 'base64'));
      delete row.png;
    }
  }
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
  console.log(`${'tier'.padEnd(9)}${'stand'.padEnd(24)}${'px'.padStart(5)}`
    + `${'frame ms'.padStart(10)}${'cpu ms'.padStart(9)}${'worst'.padStart(8)}`
    + `${'triangles'.padStart(12)}${'calls'.padStart(7)}`);
  for (const row of pass.rows) {
    console.log(`${row.level.padEnd(9)}${row.stand.padEnd(24)}${String(row.pixelRatio).padStart(5)}`
      + `${row.frame.toFixed(1).padStart(10)}${row.cpu.toFixed(1).padStart(9)}`
      + `${row.worst.toFixed(1).padStart(8)}${row.triangles.toLocaleString().padStart(12)}`
      + `${String(row.calls).padStart(7)}`);
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
if (jsonOut) {
  fs.writeFileSync(jsonOut, `${JSON.stringify({ ticket: 'T-2099',
    tree: wantSource ? 'source' : 'published', year: YEAR, frames: FRAMES, warmup: WARMUP,
    throttle: THROTTLE, passes }, null, 2)}\n`);
  console.log(`\nwritten ${jsonOut}`);
}
process.exit(bad ? 1 : 0);
