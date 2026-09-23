/**
 * T-0093 — WHAT THE VERGE IS WRITTEN THROUGH, PER LAYER, IN THE BAND THE NEAR
 * RING HANDS OVER IN.
 *
 *   node tools/measure_near_verge.mjs [--source] [--gate] [--stand ID]...
 *                                     [--viewport mobile|desktop] [--json]
 *                                     [--out DIR]
 *
 * THE QUESTION. T-0086 closed the far sward's outer edge by replacing a coverage
 * ramp with a density handover, and said in its own STATUS entry that it had NOT
 * touched "the near ring's own outer dither at 5–7.6 m". T-0093 is that residue:
 * a walker on the verge sees a patch of speckled grass a few paces ahead. The
 * ticket names `TUNE.near` as the author of it.
 *
 * **This tool exists to test that attribution before a parameter is touched**,
 * because the obvious knob is not reliably the one that draws the artefact — the
 * road's middle distance (T-0114) had its prime suspect refuted by doubling it
 * and reading the same number back. So nothing here is asked of `TUNE.near`. It
 * is asked of the FRAME, per instanced set, and the near ring is one of five
 * answers it can give.
 *
 * WHAT A SCREEN-DOORED PIXEL IS, exactly. `flora.js`'s plant shader resolves a
 * ring's coverage ramp with an ordered 4x4 Bayer matrix keyed on `gl_FragCoord`:
 *
 *     if (vChiFade < 1.0 && fract(chiBayer4(gl_FragCoord.xy) + vChiDither) >= vChiFade) discard;
 *
 * The guard is the whole of it: an instance whose own ring puts it at coverage
 * 1.0 never enters the branch and is written solid. So "is this plant drawn
 * through a screen door" is decided per INSTANCE, off the four numbers in its own
 * `aChiRing` and its distance from the camera, and it can be read back exactly:
 *
 *   partial ...... instances with 0 < fade < 1. Every fragment of one of these
 *                  is thresholded against the Bayer matrix. These, and only
 *                  these, are the dots.
 *   whole ........ instances at fade == 1. Written solid, and the CONTROL: the
 *                  same species, the same light, the same archetype, no dither.
 *   absent ....... fade == 0. Collapsed to a point by the vertex program.
 *
 * WHAT IT REPORTS.
 *
 *   dithered area .. the union of the drawn footprints of the partial instances,
 *                    less the footprints of the solid ones standing in front of
 *                    them, as a share of the frame. A count of instances is not
 *                    the artefact — a hundred plants at forty metres are four
 *                    pixels — and the ticket's complaint is about SCREEN.
 *   nyquist ........ measured on the real frame inside that region: the mean
 *                    one-pixel lightness step over the mean two-pixel one.
 *                    **This is the reading that says "speckle" rather than
 *                    "grass".** A 4x4 ordered dither at half coverage keeps
 *                    alternate columns, so its energy sits at the sampling limit
 *                    and the ratio runs above 1; ordinary image content is
 *                    smoother at one pixel than at two and runs below it. The
 *                    solid near tufts in the same frame are printed beside it as
 *                    the control, so the number is anchored to this scene's own
 *                    grass and not to a constant chosen here.
 *
 * ONE MEASURED PIXEL IS ONE DRAWING-BUFFER PIXEL, and that is why the mobile
 * context here runs at `deviceScaleFactor: 1.5` where the smoke runs at 2. The
 * screen door is locked to `gl_FragCoord`, so it has a four-pixel period in the
 * DRAWING BUFFER; the phone's buffer is 585 px wide (`main.js` caps the pixel
 * ratio at 1.5 on a coarse pointer) and a screenshot taken at 2 resamples that
 * by 4/3, smearing the exact thing being measured. At 1.5 the screenshot and the
 * buffer are the same raster. The frame drawn is the phone's own frame either
 * way — what changes is only whether the instrument can see its grain.
 *
 * Defaults to the PUBLISHED mirror, for the reason every measurement here does:
 * the source tree and the site do not load the same geometry. `--source`
 * measures the working tree instead.
 *
 * `--gate` exits non-zero when a stand's dithered-area share is above
 * `MAX_DITHERED_SHARE` or its band nyquist is above `MAX_BAND_NYQUIST`, against
 * `tools/near_verge_baseline.json`. It renders frames, so it needs Playwright and
 * cannot run inside `tools/check.sh` — that is the fast half of the two-speed
 * build and has no browser by design.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { decodePng, labL } from './critic_metrics.mjs';

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
const argv = process.argv.slice(2);
const flagVals = (name) => {
  const out = [];
  for (let i = 0; i < argv.length; i++) if (argv[i] === name) out.push(argv[i + 1]);
  return out;
};
const wantSource = argv.includes('--source');
const wantGate = argv.includes('--gate');
const asJson = argv.includes('--json');
const OUT = flagVals('--out')[0] ? path.resolve(flagVals('--out')[0]) : null;
const PICK = flagVals('--stand');
const ONLY_VIEW = flagVals('--viewport')[0] || '';
const ROOT = wantSource
  ? path.resolve(HERE, '..')
  : path.resolve(HERE, '../../../site/chicago/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.VERGE_PORT || 4197);
const YEAR = process.env.VERGE_YEAR || '1835';
const BASELINE = path.join(HERE, 'near_verge_baseline.json');

/**
 * THE STANDS. The two the far-sward run photographed, plus open prairie — the
 * three the ticket's acceptance names.
 *
 * The two town stands are read off `data/streets/1835.json` rather than guessed:
 * Wells runs north to [330.5, 7], which is where it meets South Water, and Lake
 * crosses it at [329.8, -112.4]. Each stand is set back along its own street so
 * the crossing is ahead of the walker, at the bearing the far-sward run used.
 * The prairie stand is south of the settled-town polygon and of the timber, on
 * ground `z01`/`z02` plant and no building stands on.
 *
 * `south-water-verge` is the fourth, and it is here because the first reading
 * off the other three turned up something the ticket does not say: **South
 * Water's centreline carries no near tufts at all.** The travel track is 10.5 m
 * wide and `station()` clears every plant off it, so a walker standing in the
 * roadway has the whole near ring inside cleared ground and the verge is off to
 * one side. That stand is kept as it was — it is the one the far-sward run used
 * — and this one steps the walker to the south edge of the track, which is
 * where the word "verge" actually points.
 */
const STANDS = [
  { id: 'south-water-at-wells', e: 305, n: 6.6, yaw: 84,
    why: 'South Water approaching Wells, the far-sward run\'s first stand' },
  { id: 'south-water-verge', e: 305, n: 0.6, yaw: 84,
    why: 'the same approach from the south edge of the 10.5 m travel track' },
  { id: 'wells-at-lake', e: 329.9, n: -87, yaw: 185,
    why: 'Wells approaching Lake, the far-sward run\'s second stand' },
  { id: 'open-prairie', e: 60, n: -330, yaw: 180,
    why: 'open prairie south of the town, nothing built inside the rings' },
];

/**
 * THE VIEWPORTS, and the detail level each one actually boots into. `main.js`
 * picks `light` on a coarse pointer and `full` otherwise, so these are the HIGH
 * and the LOW the ticket asks for rather than two settings chosen here. The
 * mobile scale factor is the drawing-buffer argument in the header.
 */
const VIEWPORTS = [
  { id: 'mobile', width: 390, height: 780, touch: true, scale: 1.5, detail: 'light' },
  { id: 'desktop', width: 1280, height: 800, touch: false, scale: 1, detail: 'full' },
];

/** Sets whose ring can put them at partial coverage. `flora-far` is on
 *  `FAR_RING` and never enters the dither branch; it is read anyway, so that
 *  claim is asserted here rather than assumed. */
const ROOTED = ['flora-near', 'flora-mid', 'flora-forb', 'flora-rosette', 'flora-shrub'];

/**
 * THE GATE, and it is one bar rather than three.
 *
 * **`handoverShare` must be zero.** Not small — zero. A boundary handed over by
 * density cannot produce a coverage strictly between 0 and 1, so a single plant
 * caught mid-ramp on the near ring's outer edge or the mid ring's inner edge is
 * a regression of T-0093 and not a tolerance to be tuned. It is scored on those
 * two boundaries alone, deliberately: the mid and forb rings' OUTER ramps still
 * dither, and at `light` detail they reach in as far as 5.4 m and 7.4 m, so a
 * bar on the whole frame would either fail on ground this ticket never claimed
 * or have to be slackened until it proved nothing.
 *
 * `ditheredShare` — every screen-doored plant in the verge, whatever ramp made
 * it so — is banked in `near_verge_baseline.json` and held against regression
 * rather than against a constant, so the residue above is recorded and cannot
 * quietly grow.
 *
 * THERE IS NO BAR ON THE GRAIN READING, and that is a measurement result rather
 * than an omission. Taken before the fix, the band the eye plainly reads as a
 * mesh of dots scored 0.97 down / 0.92 across in open prairie against a solid
 * control of 1.28 / 1.06 — the wrong side of its own control. The reason is
 * dilution: a bounding box round a tuft is mostly air and neighbouring blades,
 * and a discarded fragment usually reveals another plant of nearly the same
 * green rather than bare ground. So the grain is printed as a diagnostic and
 * the claim rests on the plant-by-plant reading, which is exact.
 */
const MAX_HANDOVER_SHARE = 0;
/** The verge: how far out a plant still counts as "just ahead of the walker".
 *  The near ring reaches 7.6 m at full detail and 4.6 m at light, so this covers
 *  the whole of the near/mid handover at both. */
const BAND_M = 9.0;
/** A footprint has to be worth counting. One pixel of a plant at 9 m is not a
 *  band of dots, and summing them would let a distant fringe answer for the
 *  verge. */
const MIN_FOOTPRINT_PX = 4;

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown',
};
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (url.endsWith('/')) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.writeHead(404); res.end('not found'); return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(PORT, r));
const base = `http://127.0.0.1:${PORT}`;

/**
 * The per-instance read. Everything here is taken off the buffers that went to
 * the GPU — the instance matrix, `aFlora` and `aChiRing` — so it is a reading of
 * the drawing and not of an intention. `fade` is the vertex program's own
 * expression, copied line for line.
 */
function pageRead({ stand, bandM, minPx }) {
  const a = window.__chicago4d;
  const cam = a.camera;
  cam.updateMatrixWorld(true);
  const W = a.renderer.domElement.clientWidth;
  const H = a.renderer.domElement.clientHeight;
  const bufW = a.renderer.domElement.width;
  const bufH = a.renderer.domElement.height;
  const V = new cam.position.constructor();
  const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);

  const project = (x, y, z) => {
    V.set(x, y, z);
    V.project(cam);
    return { x: (V.x * 0.5 + 0.5) * W, y: (-V.y * 0.5 + 0.5) * H, z: V.z };
  };

  const sets = {};
  const boxes = [];
  a.flora.group.traverse((m) => {
    if (!m.isInstancedMesh || !m.count) return;
    const mm = m.instanceMatrix.array;
    const fa = m.geometry.getAttribute('aFlora');
    const rgAttr = m.geometry.getAttribute('aChiRing');
    if (!fa || !rgAttr) return;
    const fl = fa.array;
    const rg = rgAttr.array;
    const row = sets[m.name] = { whole: 0, partial: 0, absent: 0, handover: 0,
      partialNear: 0, dMin: Infinity, dMax: 0, fadeMin: 1, fadeMax: 0 };
    for (let i = 0; i < m.count; i++) {
      const o = i * 16;
      const x = mm[o + 12]; const y = mm[o + 13]; const z = mm[o + 14];
      const d = Math.hypot(x - cam.position.x, z - cam.position.z);
      const r0 = rg[i * 4]; const r1 = rg[i * 4 + 1];
      const r2 = rg[i * 4 + 2]; const r3 = rg[i * 4 + 3];
      let fade = clamp01((r0 - d) / Math.max(r1, 1e-4));
      if (r3 > 0) fade *= clamp01((d - r2) / r3);
      const kind = fade <= 0 ? 'absent' : fade >= 1 ? 'whole' : 'partial';
      // WHICH BOUNDARY made it partial. The ring has two, and T-0093 converts
      // one of each: the near ring's OUTER edge and the mid ring's INNER edge.
      // A pixel written through the screen door by the mid ring's outer ramp at
      // 5-12 m on a phone is a real defect and it is NOT this ticket's, so the
      // gate has to be able to tell them apart rather than scoring them
      // together.
      const outerTerm = clamp01((r0 - d) / Math.max(r1, 1e-4));
      const innerTerm = r3 > 0 ? clamp01((d - r2) / r3) : 1;
      const onOuter = outerTerm > 0 && outerTerm < 1;
      const onInner = innerTerm > 0 && innerTerm < 1;
      const handover = d <= bandM
        && ((m.name === 'flora-near' && onOuter) || (m.name === 'flora-mid' && onInner));
      if (handover) row.handover++;
      row[kind]++;
      if (kind === 'absent') continue;
      if (kind === 'partial') {
        row.fadeMin = Math.min(row.fadeMin, fade);
        row.fadeMax = Math.max(row.fadeMax, fade);
        row.dMin = Math.min(row.dMin, d);
        row.dMax = Math.max(row.dMax, d);
        if (d <= bandM) row.partialNear++;
      }
      // The drawn extent: the record's own height and the archetype's own
      // spread, which is what `aFlora` carries and what the head-support gate
      // reads a plant's top and reach out of.
      const hM = fl[i * 4];
      const rM = Math.max(fl[i * 4 + 1], 0.05);
      let x0 = Infinity; let x1 = -Infinity; let y0 = Infinity; let y1 = -Infinity;
      let behind = false;
      for (const dx of [-rM, rM]) {
        for (const dz of [-rM, rM]) {
          for (const dy of [0, hM]) {
            const p = project(x + dx, y + dy, z + dz);
            if (p.z < -1 || p.z > 1) { behind = true; break; }
            if (p.x < x0) x0 = p.x;
            if (p.x > x1) x1 = p.x;
            if (p.y < y0) y0 = p.y;
            if (p.y > y1) y1 = p.y;
          }
        }
      }
      if (behind || x1 <= x0 || y1 <= y0) continue;
      if ((x1 - x0) * (y1 - y0) < minPx) continue;
      boxes.push({ set: m.name, kind, handover, d, x0, y0, x1, y1 });
    }
  });
  return { sets, boxes, cssWidth: W, cssHeight: H, bufWidth: bufW, bufHeight: bufH,
    detail: a.detail, stand: stand.id };
}

/** Union area of a set of boxes, rasterised onto the frame's own grid. */
function rasterise(boxes, W, H) {
  const mask = new Uint8Array(W * H);
  for (const b of boxes) {
    const x0 = Math.max(0, Math.floor(b.x0));
    const x1 = Math.min(W - 1, Math.ceil(b.x1));
    const y0 = Math.max(0, Math.floor(b.y0));
    const y1 = Math.min(H - 1, Math.ceil(b.y1));
    for (let y = y0; y <= y1; y++) {
      const row = y * W;
      for (let x = x0; x <= x1; x++) mask[row + x] = 1;
    }
  }
  return mask;
}

function countMask(mask) {
  let n = 0;
  for (let i = 0; i < mask.length; i++) if (mask[i]) n++;
  return n;
}

/**
 * THE GRAIN READING. Mean |L* step| at one pixel over mean |L* step| at two,
 * over the pixels of `mask` whose partners are also inside it — measured along
 * BOTH axes, and reported as the worse of the two.
 *
 * The 4x4 Bayer matrix's first row is 0, 8, 2, 10 — thresholds 0.03, 0.53,
 * 0.16, 0.66 — so at half coverage a row keeps alternate columns and the
 * pattern's period is TWO pixels. That is the sampling limit, where a one-pixel
 * step is large and a two-pixel step is near zero; ordinary image content is the
 * other way round, smoother at one pixel than at two.
 *
 * BOTH AXES, and the first cut of this tool measured only x, which was a
 * mistake worth recording: a grass blade is NEAR-VERTICAL and a few pixels wide,
 * so a horizontal reading is taken across the blade — where a solid sward is
 * already at the sampling limit — while the screen door's own carving of that
 * blade runs DOWN it. The horizontal reading came back 0.91 in a band the eye
 * reads as a mesh of dots, against 1.07 for the solid control: no signal, and
 * the wrong sign. The vertical one is asked along the blade, where a solid blade
 * is smooth and a screen-doored one is a dotted line.
 */
function nyquist(img, mask) {
  const W = img.width; const H = img.height;
  const L = (x, y) => {
    const i = (y * W + x) * 4;
    return labL(img.data[i], img.data[i + 1], img.data[i + 2]);
  };
  const axis = (dx, dy) => {
    let s1 = 0; let n1 = 0; let s2 = 0; let n2 = 0;
    for (let y = 0; y + 2 * dy < H; y++) {
      for (let x = 0; x + 2 * dx < W; x++) {
        const at = y * W + x;
        if (!mask[at]) continue;
        const l0 = L(x, y);
        if (mask[at + dy * W + dx]) { s1 += Math.abs(l0 - L(x + dx, y + dy)); n1++; }
        if (mask[at + 2 * dy * W + 2 * dx]) { s2 += Math.abs(l0 - L(x + 2 * dx, y + 2 * dy)); n2++; }
      }
    }
    if (!n1 || !n2 || s2 === 0) return null;
    return { ratio: (s1 / n1) / (s2 / n2), step1: s1 / n1, step2: s2 / n2, pixels: n1 };
  };
  const x = axis(1, 0);
  const y = axis(0, 1);
  if (!x || !y) return null;
  const worst = y.ratio >= x.ratio ? y : x;
  return { ...worst, axis: worst === y ? 'down' : 'across', across: round(x.ratio, 3),
    down: round(y.ratio, 3) };
}

async function openPage(browser, vp) {
  const ctx = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    hasTouch: vp.touch,
    isMobile: false,
    deviceScaleFactor: vp.scale,
  });
  const page = await ctx.newPage();
  page.setDefaultTimeout(90_000);
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(`${base}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
  // Eight minutes, not four. On a SwiftShader runner the published mirror boots
  // in about four and `--source`, which loads the uncompressed masters, does
  // not — measured, after a `--source` run died on a 240 s bar with a healthy
  // page behind it. And a stall is DIAGNOSED rather than reported as a timeout:
  // "the page did not become ready" and "the renderer threw while placing the
  // sward" look identical from out here, and telling them apart by re-running
  // costs ten minutes a go.
  try {
    await page.waitForFunction(() => window.__chicago4d?.ready === true, null,
      { timeout: 480000 });
  } catch (e) {
    const state = await page.evaluate(() => ({
      ready: window.__chicago4d?.ready,
      error: String(window.__chicago4d?.error ?? ''),
      problems: (window.__chicago4d?.problems ?? []).slice(0, 10),
      gate: document.getElementById('gate-sub')?.textContent,
    })).catch((x) => ({ evaluateFailed: String(x) }));
    console.log(`\nSTALLED at ${vp.id}: ${JSON.stringify(state, null, 2)}`);
    console.log(`pageerrors: ${JSON.stringify(errors.slice(0, 10), null, 2)}`);
    throw e;
  }
  const gate = await page.$('#gate button, .gate button');
  if (gate) { await gate.click(); await page.waitForTimeout(1200); }
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      if (/got it/i.test(b.textContent ?? '')) b.click();
    }
  });
  return { ctx, page, errors };
}

const results = [];
const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  // SwiftShader is the only GPU here — `tools/smoke_renderer.mjs` says the same.
  args: ['--enable-unsafe-swiftshader'],
});

for (const vp of VIEWPORTS) {
  if (ONLY_VIEW && vp.id !== ONLY_VIEW) continue;
  const { ctx, page, errors } = await openPage(browser, vp);
  const booted = await page.evaluate(() => window.__chicago4d.detail);
  for (const stand of STANDS) {
    if (PICK.length && !PICK.includes(stand.id)) continue;
    await page.evaluate((s) => {
      const a = window.__chicago4d;
      a.setFly(false);
      a.walker.teleport({ local_e: s.e, local_n: s.n, yaw_deg: s.yaw });
      a.setAnimationHold(true);
      for (const id of ['hud', 'popup']) {
        const el = document.getElementById(id);
        if (el) { el.dataset.vergeHidden = el.style.visibility; el.style.visibility = 'hidden'; }
      }
      // Two steps: the first carries the teleport into the lattice rebuild, the
      // second draws the field the rebuild placed.
      a.step(); a.step(); a.step();
    }, stand);
    await page.waitForTimeout(350);
    const read = await page.evaluate(pageRead,
      { stand, bandM: BAND_M, minPx: MIN_FOOTPRINT_PX });
    const shotBuf = await page.screenshot({ type: 'png' });
    await page.evaluate(() => {
      const a = window.__chicago4d;
      for (const id of ['hud', 'popup']) {
        const el = document.getElementById(id);
        if (el) { el.style.visibility = el.dataset.vergeHidden ?? ''; delete el.dataset.vergeHidden; }
      }
      a.setAnimationHold(false);
    });
    const img = decodePng(shotBuf);
    if (OUT) {
      fs.mkdirSync(OUT, { recursive: true });
      fs.writeFileSync(path.join(OUT, `${vp.id}-${stand.id}.png`), shotBuf);
    }
    const k = img.width / read.cssWidth;
    const scaled = read.boxes.map((b) => ({ ...b,
      x0: b.x0 * k, x1: b.x1 * k, y0: b.y0 * k, y1: b.y1 * k }));
    const W = img.width; const H = img.height;
    const frame = W * H;

    // The verge: partial instances inside the band, less the solid ones standing
    // in front of them. A plant at 6 m whose pixels are all behind a solid tuft
    // at 3 m is not a dot a visitor can see.
    const solid = rasterise(scaled.filter((b) => b.kind === 'whole'), W, H);
    const bandBoxes = scaled.filter((b) => b.kind === 'partial' && b.d <= BAND_M);
    const bandRaw = rasterise(bandBoxes, W, H);
    const band = new Uint8Array(frame);
    for (let i = 0; i < frame; i++) band[i] = bandRaw[i] && !solid[i] ? 1 : 0;
    // The control: solid near tufts, same frame, same species, no dither.
    const control = rasterise(
      scaled.filter((b) => b.kind === 'whole' && b.set === 'flora-near'), W, H);

    const perSet = {};
    for (const name of ROOTED.concat(['flora-far'])) {
      const row = read.sets[name];
      if (!row) continue;
      const mine = rasterise(
        bandBoxes.filter((b) => b.set === name), W, H);
      let n = 0;
      let exposed = 0;
      for (let i = 0; i < frame; i++) {
        if (!mine[i]) continue;
        n++;
        if (!solid[i]) exposed++;
      }
      perSet[name] = {
        whole: row.whole, partial: row.partial, absent: row.absent,
        handover: row.handover, partialInBand: row.partialNear,
        dRange: row.partial ? [round(row.dMin, 2), round(row.dMax, 2)] : null,
        fadeRange: row.partial ? [round(row.fadeMin, 3), round(row.fadeMax, 3)] : null,
        vergePixels: n, vergeShare: round(n / frame, 5),
        exposedPixels: exposed, exposedShare: round(exposed / frame, 5),
      };
    }

    const bandPx = countMask(bandRaw);
    const exposedPx = countMask(band);
    // THE HANDOVER ITSELF — the two boundaries this ticket converts, and the
    // only figure the gate is allowed to be strict about. It goes to exactly
    // zero when both are density handovers, because a spread boundary cannot
    // produce a fade strictly between 0 and 1.
    const handoverMask = rasterise(scaled.filter((b) => b.handover), W, H);
    const handoverPx = countMask(handoverMask);
    const handoverPlants = Object.values(read.sets)
      .reduce((a, s) => a + s.handover, 0);
    const row = {
      viewport: vp.id, detail: booted, stand: stand.id, why: stand.why,
      frame: [W, H], buffer: [read.bufWidth, read.bufHeight],
      rasterMatches: read.bufWidth === W && read.bufHeight === H,
      // THE HEADLINE NUMBER: the union of the drawn footprints of every
      // partially-covered plant inside the verge, as a share of the frame — the
      // ground over which the screen door is operating at all.
      ditheredPixels: bandPx,
      ditheredShare: round(bandPx / frame, 5),
      // ...and the part of it that is not behind a solid plant. Bounding boxes
      // cannot model occlusion properly, so this is a floor and the one above is
      // a ceiling; the grain below is read on this one, where the dithered
      // plants are the frontmost thing.
      exposedPixels: exposedPx,
      exposedShare: round(exposedPx / frame, 5),
      handoverPlants,
      handoverPixels: handoverPx,
      handoverShare: round(handoverPx / frame, 5),
      bandNyquist: nyquist(img, band),
      controlNyquist: nyquist(img, control),
      sets: perSet,
      pageErrors: errors.slice(0, 5),
    };
    results.push(row);
    if (!asJson) print(row);
  }
  await ctx.close();
}
await browser.close();
server.close();

function round(v, p = 3) {
  if (v === null || v === undefined || !Number.isFinite(v)) return null;
  const m = 10 ** p;
  return Math.round(v * m) / m;
}

function print(r) {
  console.log(`\n${r.viewport} (${r.detail}) — ${r.stand}`);
  console.log(`  ${r.why}`);
  if (!r.rasterMatches) {
    console.log(`  !! screenshot ${r.frame.join('x')} is not the drawing buffer `
      + `${r.buffer.join('x')} — the grain reading is resampled and void`);
  }
  console.log(`  NEAR/MID handover:   ${r.handoverPlants} plant(s) mid-ramp, `
    + `${(r.handoverShare * 100).toFixed(3)}% of the frame  <- the gate`);
  console.log(`  screen-doored verge: ${r.ditheredPixels} px, `
    + `${(r.ditheredShare * 100).toFixed(3)}% of the frame `
    + `(${(r.exposedShare * 100).toFixed(3)}% not behind a solid plant)`);
  const n = r.bandNyquist; const c = r.controlNyquist;
  console.log(`  grain in that band:  ${n ? n.ratio.toFixed(3) : 'n/a'}`
    + `${n ? ` [${n.axis}] (1px ${n.step1.toFixed(2)} L*, 2px ${n.step2.toFixed(2)} L*, `
      + `across ${n.across}, down ${n.down}, ${n.pixels} px)` : ''}`);
  console.log(`  grain, solid tufts:  ${c ? c.ratio.toFixed(3) : 'n/a'}`
    + `${c ? ` [${c.axis}] (across ${c.across}, down ${c.down}, ${c.pixels} px)`
      + '  <- the control' : ''}`);
  for (const [name, s] of Object.entries(r.sets)) {
    console.log(`    ${name.padEnd(15)} whole ${String(s.whole).padStart(5)}  `
      + `partial ${String(s.partial).padStart(5)}  in-band ${String(s.partialInBand).padStart(4)}  `
      + `handover ${String(s.handover).padStart(4)}  `
      + `verge ${String(s.vergePixels).padStart(6)} px `
      + `(${(s.vergeShare * 100).toFixed(3)}%, exposed `
      + `${(s.exposedShare * 100).toFixed(3)}%)`
      + (s.dRange ? `  d ${s.dRange[0]}-${s.dRange[1]} m` : ''));
  }
  for (const e of r.pageErrors) console.log(`  pageerror: ${e}`);
}

if (asJson) console.log(JSON.stringify(results, null, 2));

if (wantGate) {
  const bad = [];
  for (const r of results) {
    if (!r.rasterMatches) bad.push(`${r.viewport}/${r.stand}: raster mismatch`);
    if (r.handoverShare > MAX_HANDOVER_SHARE || r.handoverPlants > 0) {
      bad.push(`${r.viewport}/${r.stand}: ${r.handoverPlants} plant(s) caught mid-ramp on the `
        + `near/mid handover, covering ${(r.handoverShare * 100).toFixed(3)}% of the frame — `
        + 'that boundary is supposed to be a density handover and cannot produce a partial '
        + 'coverage at all');
    }
    if (r.pageErrors.length) bad.push(`${r.viewport}/${r.stand}: ${r.pageErrors[0]}`);
  }
  if (fs.existsSync(BASELINE)) {
    const banked = JSON.parse(fs.readFileSync(BASELINE, 'utf8'));
    for (const r of results) {
      const was = banked.stands?.[`${r.viewport}/${r.stand}`];
      if (!was) continue;
      // The residue — the mid and forb rings' own outer ramps, which T-0093
      // does not touch — held against the banked figure so it is recorded and
      // cannot grow back quietly. A legitimate improvement re-banks it in the
      // same commit; the slack is a tenth of a per cent of the frame, for the
      // handful of pixels a rebuild boundary can move a bounding box by.
      if (r.ditheredShare > was.ditheredShare + 0.001) {
        bad.push(`${r.viewport}/${r.stand}: screen-doored verge grew `
          + `${(was.ditheredShare * 100).toFixed(3)}% -> `
          + `${(r.ditheredShare * 100).toFixed(3)}% of the frame`);
      }
    }
  } else {
    console.log(`\n(no ${path.basename(BASELINE)} — the residue is unheld)`);
  }
  console.log(bad.length ? `\nGATE FAIL\n  ${bad.join('\n  ')}` : '\nGATE PASS');
  process.exit(bad.length ? 1 : 0);
}
