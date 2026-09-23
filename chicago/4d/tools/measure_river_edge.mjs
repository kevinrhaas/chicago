/**
 * ROADMAP R-BUG1 — DOES THE RIVER EDGE FLICKER WHEN FLYING?
 *
 *   node tools/measure_river_edge.mjs [--source] [--gate] [--out DIR]
 *
 * The owner reported it as motion: fly over the river and its edges shimmer.
 * Motion is the hard part to measure — a camera that moves photographs a
 * different scene, so a diff between two frames of a flight is mostly the
 * flight. This asks the question a different way, and the difference is the
 * whole instrument:
 *
 *   **move the camera two millimetres and photograph it again.**
 *
 * At 175 m and a 62-degree field of view, 2 mm is about a five-hundredth of a
 * pixel. No edge in the scene can move. Nothing is re-dealt: the flora and tree
 * rings rebuild on a metre-scale threshold, the clock is held so the wind does
 * not blow, and the HUD is hidden. So a pixel that CHANGES between those two
 * frames changed for one reason — two surfaces are tied in the depth buffer and
 * the tie resolved the other way. That is z-fighting, and z-fighting under a
 * moving camera is exactly what a visitor sees as flicker.
 *
 * The control is part of the measurement, not a nicety: the same pose is also
 * photographed twice with NO nudge at all. If that pair differs, the harness is
 * measuring its own noise and every number below is void. It is printed either
 * way.
 *
 * `--gate` exits non-zero when a station's nudged pair differs by more than
 * `MAX_FLICKER_FRACTION` of the frame. The threshold is not a taste: the
 * control pair is zero, so anything above the noise floor is a tie somewhere,
 * and the fraction only allows for a handful of stray pixels rather than a
 * band along the bank.
 *
 * Defaults to the PUBLISHED mirror for the reason every other measurement here
 * does — the source tree and the site do not load the same geometry, and depth
 * precision is a property of what actually ships. `--source` measures the
 * working tree instead.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { decodePng } from './critic_metrics.mjs';

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
const wantSource = process.argv.includes('--source');
const wantGate = process.argv.includes('--gate');
/**
 * A DIAGNOSTIC, not a gate: drop the sun's shadow before measuring. The frame
 * flickers in places that are not the bank — roofs, walls, canopies — and the
 * shadow camera follows the walker, so a camera that moves re-rasterises the
 * shadow map onto a shifted texel grid. This flag is how that suspicion was
 * turned into a number (ROADMAP R-BUG6); it changes what is drawn and must
 * never be combined with `--gate`.
 */
const noSunShadow = process.argv.includes('--no-sun-shadow');
const outArg = process.argv.indexOf('--out');
const OUT = outArg > -1 ? path.resolve(process.argv[outArg + 1]) : null;
const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.RIVER_PORT || 4193);
const YEAR = process.env.RIVER_YEAR || '1835';

/** The nudge, in metres. Sub-pixel at every station below by three orders of
 *  magnitude — see the header.
 *
 *  `RIVER_NUDGE_M` overrides it, and R-BUG6 is why: 2 mm slides the shadow map's
 *  texel grid by 1.7 % of a texel, so it catches 1.7 % of the shadow crawl a
 *  visitor walking at 1.4 m/s sees twelve texels of every second. Nudging by a
 *  HALF TEXEL instead, with `--snap-off` and without, measures that crawl paired
 *  against identical parallax — the two frames have moved the camera by the same
 *  amount, so the difference between the two numbers is the shadow box alone. */
const NUDGE_M = Number(process.env.RIVER_NUDGE_M || 0.002);
/** R-BUG6's handle, for the paired measurement above. Not a gate run. */
const snapOff = process.argv.includes('--snap-off');
/**
 * R-BUG6 — MOVE THE SHADOW BOX AND NOT THE CAMERA.
 *
 * The nudge in the header answers a question about depth ties, and it can only
 * answer it while the nudge is far below a pixel. It is therefore the WRONG
 * instrument for the shadow box: 2 mm slides the box by 1.7 % of a texel, and a
 * nudge big enough to slide it a whole texel (58.6 mm here) also resamples the
 * whole frame — measured 2026-08-17 at `from_above`, where a half-texel nudge
 * changes ~29,000 pixels with the snap on and ~28,800 with it off, so the camera
 * move swamps the thing being measured and even reverses its sign.
 *
 * So this drift holds the camera perfectly still and moves the BOX: `follow` is
 * frozen for the duration, the box is placed twice half a texel apart, and the
 * two frames are photographed from one identical pose. Every pixel of the
 * difference is the shadow map re-quantising, which is what a walking visitor
 * sees as crawl along an eave line. With the snap on the two placements round to
 * the same lattice cell and the difference is zero, which is the fix stated as a
 * measurement rather than as an invariant.
 */
const boxDrift = process.argv.includes('--box-drift');
/** A changed pixel: any channel moved by more than this. 8-bit sRGB output, so
 *  2 counts is above dither and far below a surface swap (water against bank is
 *  tens of counts). */
const CHANNEL_EPS = 2;
/** How far from the drawn bank line a changed pixel still counts as the bank
 *  flickering. Two pixels: an edge is a pixel wide and its shading neighbours
 *  move with it. */
const BANK_RADIUS_PX = 2;
/**
 * THE GATE, and it is a SHARE of the bank line rather than a pixel count,
 * because a pixel count is a number about the pose. Today's frames put 4–8 % of
 * their pixels within two of a waterline; a count that passed at one altitude
 * would be meaningless at another. This asks the question the owner asked:
 * **how much of the river's edge changes when the camera moves two
 * millimetres?**
 */
const MAX_BANK_FLICKER_SHARE = 0.05;

/**
 * THE STATIONS — aerial, over water, along the owner's own reproduction.
 *
 * "Fly to the `from_above` anchor, then descend slowly toward the forks." The
 * first station is that anchor as the scene defines it; the other two are the
 * descent, at the two altitudes where the main stem and the forks fill the
 * frame. All three look at the river, because a station that cannot see the
 * bank line cannot answer the question — `waterPixels` is reported per station
 * so a pose that stops seeing water fails loudly rather than passing quietly.
 */
const PICK = (process.env.RIVER_STATIONS || '').split(',').map((s) => s.trim()).filter(Boolean);
const STATIONS = [
  { id: 'from_above', label: 'The scene anchor — the whole town from 175 m',
    pose: { local_e: 60, local_n: -330, yaw_deg: 0, altitude_m: 175, pitch_deg: -30 } },
  { id: 'descend_main_stem', label: 'Descending to 90 m, the main stem across the frame',
    pose: { local_e: 40, local_n: -150, yaw_deg: 20, altitude_m: 90, pitch_deg: -25 } },
  { id: 'over_the_forks', label: 'Over Wolf Point at 45 m, both branches in view',
    pose: { local_e: -60, local_n: -60, yaw_deg: 40, altitude_m: 45, pitch_deg: -20 } },
].filter((s) => !PICK.length || PICK.includes(s.id));
if (!STATIONS.length) {
  console.error(`no station matches RIVER_STATIONS=${process.env.RIVER_STATIONS}`);
  process.exit(2);
}

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown',
};
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file)) {
    res.writeHead(404, { 'content-type': 'text/plain' });
    res.end(`not found: ${url}`);
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(PORT, r));
if (!wantSource && !fs.existsSync(path.join(ROOT, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`);
  process.exit(2);
}
if (OUT) fs.mkdirSync(OUT, { recursive: true });
console.log(`serving ${ROOT} — ${wantSource ? 'source tree' : 'PUBLISHED mirror'}\n`);

const VIEWPORT = process.env.RIVER_VIEWPORT === 'mobile'
  ? { width: 390, height: 780 } : { width: 1280, height: 800 };
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: VIEWPORT });
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
// Hold the clock before ready, the way critic_shots.mjs does: the wind must not
// blow between two frames that are meant to differ only in the depth buffer.
await page.waitForFunction(() => {
  const api = window.__chicago4d;
  if (typeof api?.setAnimationHold !== 'function') return false;
  api.setAnimationHold(true);
  return true;
}, null, { polling: 'raf', timeout: 240_000 });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 240_000 });
const gate = await page.$('#gate-btn');
if (gate) await page.click('#gate-btn');
await page.evaluate(() => {
  for (const b of document.querySelectorAll('button')) {
    if (/got it|dismiss|close/i.test(b.textContent ?? '')) b.click();
  }
  const style = document.createElement('style');
  style.textContent = 'body > *:not(#view) { visibility: hidden !important; }';
  document.head.append(style);
});

/**
 * PUT THE SHADOW MAP IN OR OUT OF THE FRAME, and reach the render doing it.
 *
 * The first version of this diagnostic dropped `sun.castShadow` after boot and
 * changed **0 pixels**, which is what ROADMAP R-BUG6 means by "the shadow
 * suspect is untested, not refuted". The reason is compilation: `castShadow` is
 * read when a material's program is built, so flipping it later leaves every
 * shader in the scene still sampling `directionalShadowMap[0]` — and the map
 * itself is still hanging in the texture unit from the last frame that had one.
 * The scene keeps its shadows and the flag reports success.
 *
 * So the handle is the shadow map's own switch plus a recompile: every material
 * in the scene is marked `needsUpdate`, which rebuilds each program against the
 * new `NUM_DIR_LIGHT_SHADOWS`. That is what actually takes the shadow out of the
 * picture, and the liveness proof below is the number that says so.
 */
async function setSunShadow(on) {
  return page.evaluate(async (want) => {
    const api = window.__chicago4d;
    api.renderer.shadowMap.enabled = want;
    api.scene3d.traverse((o) => {
      const m = o.material;
      if (!m) return;
      for (const one of Array.isArray(m) ? m : [m]) one.needsUpdate = true;
    });
    for (let i = 0; i < 4; i++) await api.capture(4);
    return api.renderer.shadowMap.enabled;
  }, on);
}

if (snapOff) {
  const was = await page.evaluate(() => window.__chicago4d.world.setShadowSnap(false));
  if (was !== false) {
    console.error('the shadow snap would not switch off — the paired measurement is void');
    process.exit(2);
  }
  console.log('DIAGNOSTIC: the shadow box follows the camera unquantised (R-BUG6 before).'
    + '\nNot a gate run.\n');
}

if (noSunShadow) {
  if (!(await page.evaluate(() => !!window.__chicago4d?.renderer?.shadowMap))) {
    console.error('no renderer on the harness — the shadow diagnostic cannot run');
    process.exit(2);
  }
  await setSunShadow(false);
  console.log('DIAGNOSTIC: the shadow map is switched off and every material recompiled '
    + 'without it.\nNot a gate run.\n');
}

/**
 * THE FRAME IS TAKEN OFF THE PAGE, NOT OFF THE ELEMENT, and the assertion below
 * is what makes those the same picture.
 *
 * `elementHandle.screenshot()` waits for the element to be *stable* — two
 * consecutive animation frames with an unchanged box — before it fires. On a
 * runner without a GPU one frame of this scene takes about ten seconds under
 * SwiftShader, so two of them do not fit inside Playwright's 30 s action
 * timeout and every capture in this tool timed out (measured 2026-08-17, on the
 * published mirror: element capture fails at 12 s, page capture returns in
 * 10.2 s from the same page). A stability wait is the wrong wait here anyway:
 * the whole instrument holds the clock precisely so that nothing moves.
 *
 * `page.screenshot()` has no such wait, and it photographs the viewport. The
 * canvas is full-bleed at the origin, so the two are the same pixels — asserted
 * here rather than assumed, because if the canvas ever stops filling the
 * viewport this substitution would silently start measuring the page around it.
 */
const canvas = (await page.$('#view')) ?? (await page.$('canvas'));
{
  const box = await canvas.boundingBox();
  const ok = box && box.x === 0 && box.y === 0
    && box.width === VIEWPORT.width && box.height === VIEWPORT.height;
  if (!ok) {
    console.error(`the canvas does not fill the viewport (${JSON.stringify(box)} against `
      + `${VIEWPORT.width}x${VIEWPORT.height}) — a page capture would not be a frame capture`);
    process.exit(2);
  }
}
const shot = async () => decodePng(await page.screenshot());

async function stand(pose) {
  return page.evaluate(async (p) => {
    const api = window.__chicago4d;
    api.setFly(typeof p.altitude_m === 'number');
    api.walker.teleport(p);
    // Eight frames, the critic_shots idiom: the first carries the teleport and
    // the rest let the camera-driven rebuilds settle. They advance no time.
    for (let i = 0; i < 8; i++) await api.capture(4);
    return { e: api.player.e, n: api.player.n, y: api.player.y,
             flying: api.player.flying, drawCalls: api.stats().drawCalls };
  }, pose);
}

/**
 * Water, loosely. The water material is a desaturated blue-green under this sky
 * and the ground beside it is a dun, so blue over red separates them at every
 * station here. Loose on purpose: its job is to say which SIDE of the bank a
 * pixel was on, not to measure the river.
 */
const waterish = (r, g, b) => b > r + 6 && g > r;

/**
 * THE BANK LINE, in pixels: where the water mask meets the land mask.
 *
 * Measuring the whole frame answers a different question — see the note on
 * `frame_flicker_px` below, and the successor parcel it opened. The bank line
 * is what R-BUG1 is about, and it is found in the frame itself rather than
 * projected from the data, because the defect is that the drawn edge and the
 * data's edge disagree.
 */
function bankMask(img) {
  const { width: W, height: H, data } = img;
  const wet = new Uint8Array(W * H);
  for (let p = 0; p < W * H; p++) {
    const i = p * 4;
    wet[p] = waterish(data[i], data[i + 1], data[i + 2]) ? 1 : 0;
  }
  const edge = new Uint8Array(W * H);
  let n = 0;
  for (let y = 1; y < H - 1; y++) {
    for (let x = 1; x < W - 1; x++) {
      const p = y * W + x;
      const v = wet[p];
      if (v !== wet[p - 1] || v !== wet[p + 1] || v !== wet[p - W] || v !== wet[p + W]) {
        edge[p] = 1; n++;
      }
    }
  }
  return { edge, count: n, width: W, height: H };
}

/** Two frames, already decoded: how many pixels differ, how, and by how much. */
function diff(a, b, bank = null) {
  if (a.width !== b.width || a.height !== b.height) throw new Error('frame size changed');
  let changed = 0;
  let swapped = 0;
  let onBank = 0;
  let worst = 0;
  const W = a.width;
  for (let p = 0; p < W * a.height; p++) {
    const i = p * 4;
    const d = Math.max(
      Math.abs(a.data[i] - b.data[i]),
      Math.abs(a.data[i + 1] - b.data[i + 1]),
      Math.abs(a.data[i + 2] - b.data[i + 2]),
    );
    if (d > worst) worst = d;
    if (d <= CHANNEL_EPS) continue;
    changed++;
    // A pixel that was water and is now land (or the reverse) is the bank line
    // resolving the other way. It is a subset of the pixels ON the bank: an
    // edge pixel can also flip between two shades of water, which is the same
    // tie seen against a darker neighbour.
    if (waterish(a.data[i], a.data[i + 1], a.data[i + 2])
      !== waterish(b.data[i], b.data[i + 1], b.data[i + 2])) swapped++;
    if (bank) {
      const x = p % W;
      const y = (p / W) | 0;
      let near = false;
      for (let dy = -BANK_RADIUS_PX; dy <= BANK_RADIUS_PX && !near; dy++) {
        for (let dx = -BANK_RADIUS_PX; dx <= BANK_RADIUS_PX; dx++) {
          const yy = y + dy, xx = x + dx;
          if (yy < 0 || xx < 0 || yy >= a.height || xx >= W) continue;
          if (bank.edge[yy * W + xx]) { near = true; break; }
        }
      }
      if (near) onBank++;
    }
  }
  return { changed, swapped, onBank, worst, pixels: a.width * a.height };
}

// ---- the mask, for eyes rather than for the gate -------------------------- //

const CRC = (() => {
  const t = new Int32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c;
  }
  return (buf) => {
    let c = -1;
    for (let i = 0; i < buf.length; i++) c = t[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
    return (c ^ -1) >>> 0;
  };
})();

function chunk(type, body) {
  const head = Buffer.alloc(8);
  head.writeUInt32BE(body.length, 0);
  head.write(type, 4, 'ascii');
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(CRC(Buffer.concat([Buffer.from(type, 'ascii'), body])), 0);
  return Buffer.concat([head, body, crc]);
}

/** RGBA8, filter 0. Enough to write a mask a person can look at. */
function writePng(file, img) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(img.width, 0);
  ihdr.writeUInt32BE(img.height, 4);
  ihdr[8] = 8; ihdr[9] = 6;
  const stride = img.width * 4;
  const raw = Buffer.alloc((stride + 1) * img.height);
  for (let y = 0; y < img.height; y++) {
    raw[y * (stride + 1)] = 0;
    Buffer.from(img.data.buffer, img.data.byteOffset + y * stride, stride)
      .copy(raw, y * (stride + 1) + 1);
  }
  fs.writeFileSync(file, Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0)),
  ]));
}

/** The frame, with every flipped pixel painted magenta. */
function maskOf(a, b) {
  const data = new Uint8Array(a.data);
  for (let i = 0; i < a.data.length; i += 4) {
    const d = Math.max(
      Math.abs(a.data[i] - b.data[i]),
      Math.abs(a.data[i + 1] - b.data[i + 1]),
      Math.abs(a.data[i + 2] - b.data[i + 2]),
    );
    if (d > CHANNEL_EPS) { data[i] = 255; data[i + 1] = 0; data[i + 2] = 255; }
  }
  return { width: a.width, height: a.height, data };
}

/** How much water is in the frame — the proof that the bank line is in it at
 *  all. No number in the table is derived from this one. */
function waterPixels(img) {
  let n = 0;
  for (let i = 0; i < img.data.length; i += 4) {
    if (waterish(img.data[i], img.data[i + 1], img.data[i + 2])) n++;
  }
  return n;
}

const rows = [];
/**
 * Does the diagnostic reach the frame? A flag that changes nothing drawn would
 * report "the shadow is not the cause" for the same reason a broken thermometer
 * reports a steady temperature, and this project has shipped that mistake
 * before. So the first station photographs itself with the sun's shadow put
 * BACK, and the difference is printed beside the finding.
 */
let shadowEffectPx = null;
for (const st of STATIONS) {
  const arrived = await stand(st.pose);
  const a = await shot();
  if (noSunShadow && shadowEffectPx === null) {
    await setSunShadow(true);
    shadowEffectPx = diff(a, await shot()).changed;
    await setSunShadow(false);
  }
  let driftPx = null;
  if (boxDrift) {
    const driftM = await page.evaluate(async () => {
      const api = window.__chicago4d;
      api.__chiRealFollow = api.world.follow.bind(api.world);
      api.__chiBoxAt = async (dx) => {
        const p = api.camera.position;
        api.__chiRealFollow({ x: p.x + dx, y: 0, z: p.z });
        for (let i = 0; i < 2; i++) await api.capture(4);
      };
      // The loop calls `world.follow(camera.position)` every frame; freezing it
      // is what lets the box stand somewhere the camera is not.
      api.world.follow = () => {};
      await api.__chiBoxAt(0);
      return api.world.shadowRig.texelM / 2;
    });
    const held = await shot();
    await page.evaluate((d) => window.__chicago4d.__chiBoxAt(d), driftM);
    const drifted = await shot();
    driftPx = { m: driftM, changed: diff(held, drifted).changed };
    await page.evaluate(() => {
      const api = window.__chicago4d;
      api.world.follow = api.__chiRealFollow;
    });
    console.log(`  ${st.id}: moving the shadow box ${(driftM * 1000).toFixed(1)} mm `
      + `— half a texel — with the camera held still changes `
      + `${driftPx.changed} pixels`);
  }
  // The control: same pose, same everything, photographed again. Two frames of
  // an unchanged scene must be identical, and if they are not, nothing else
  // here means anything.
  const control = await shot();
  await stand({ ...st.pose, local_e: st.pose.local_e + NUDGE_M });
  const b = await shot();
  const bank = bankMask(a);
  const nudged = diff(a, b, bank);
  const still = diff(a, control, bank);
  if (OUT) {
    writePng(path.join(OUT, `${st.id}.png`), a);
    writePng(path.join(OUT, `${st.id}-flicker.png`), maskOf(a, b));
  }
  rows.push({
    id: st.id,
    label: st.label,
    altitude_m: st.pose.altitude_m,
    eye_y_m: Number(arrived.y.toFixed(3)),
    water_px: waterPixels(a),
    control_changed_px: still.changed,
    bank_px: bank.count,
    bank_flicker_px: nudged.onBank,
    bank_flicker_share: bank.count ? nudged.onBank / bank.count : 0,
    bank_swap_px: nudged.swapped,
    // Reported, NOT gated. See the note under the table.
    frame_flicker_px: nudged.changed,
    frame_flicker_fraction: nudged.changed / nudged.pixels,
    worst_channel_delta: nudged.worst,
  });
}

await browser.close();
server.close();

const w = (s, n) => String(s).padStart(n);
console.log(`R-BUG1 — the river edge under a ${NUDGE_M * 1000} mm camera nudge · `
  + `${VIEWPORT.width}x${VIEWPORT.height}`
  + `${snapOff ? ' · SHADOW SNAP OFF' : ''}${noSunShadow ? ' · NO SHADOW MAP' : ''}\n`);
console.log('station              control   bank px   bank flicker    share   swaps    whole frame');
for (const r of rows) {
  console.log(`${r.id.padEnd(20)} ${w(r.control_changed_px, 7)} ${w(r.bank_px, 9)} `
    + `${w(r.bank_flicker_px, 14)} ${w((r.bank_flicker_share * 100).toFixed(1) + ' %', 8)} `
    + `${w(r.bank_swap_px, 7)} ${w(r.frame_flicker_px, 14)}`);
}
const worstRow = rows.reduce((m, r) => (r.bank_flicker_share > m.bank_flicker_share ? r : m), rows[0]);
console.log(`\nworst station: ${worstRow.id} — ${(worstRow.bank_flicker_share * 100).toFixed(1)} % `
  + `of its bank line changes under a ${NUDGE_M * 1000} mm nudge `
  + `(gate: ${(MAX_BANK_FLICKER_SHARE * 100).toFixed(1)} %)`);
console.log('\n`whole frame` is REPORTED AND NOT GATED. It counts every changed pixel, and this'
  + '\nparcel measured that most of them are not the bank: roofs, walls and canopies flicker'
  + '\nunder the same nudge, on a cause this parcel did not chase (ROADMAP R-BUG6).');
if (noSunShadow) {
  console.log(`\nDIAGNOSTIC CONTROL: putting the sun's shadow back changes ${shadowEffectPx} pixels `
    + `of the first station's frame.`);
  if (!shadowEffectPx) {
    console.log('THE FLAG NEVER REACHED THE RENDER — dropping `castShadow` after boot leaves the '
      + 'shadow map\nand the compiled materials exactly as they were, so every number above is '
      + 'about a scene\nWITH shadows in it and this run tests nothing. Measured 2026-08-16 and '
      + 'banked on ROADMAP\nR-BUG6: the shadow suspect is UNTESTED, not refuted.');
    process.exit(2);
  }
}
if (errors.length) console.log(`\npage errors: ${errors.length}\n - ${errors.slice(0, 5).join('\n - ')}`);

const unsound = rows.filter((r) => r.control_changed_px > 0);
const dry = rows.filter((r) => r.water_px < 1000);
const failing = rows.filter((r) => r.bank_flicker_share > MAX_BANK_FLICKER_SHARE);
if (unsound.length) {
  console.log(`\nUNSOUND: ${unsound.map((r) => r.id).join(', ')} — two frames of an unchanged `
    + 'scene differ, so the nudged pair measures noise as well as ties.');
}
if (dry.length) {
  console.log(`\nNO WATER IN FRAME: ${dry.map((r) => r.id).join(', ')} — the pose does not see `
    + 'the bank line, so it cannot answer this question.');
}
if (wantGate) {
  if (unsound.length || dry.length || errors.length) process.exit(2);
  if (failing.length) {
    console.log(`\nFAIL: ${failing.map((r) => `${r.id} ${(r.bank_flicker_share * 100).toFixed(1)} %`)
      .join(', ')}`);
    process.exit(1);
  }
  console.log('\nPASS');
}
