/**
 * measure_picket_reading.mjs — does the fort's stockade READ as posts, from the
 * stands a visitor actually occupies?
 *
 *   PW_EXECUTABLE=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \
 *     node tools/measure_picket_reading.mjs [--source] [--out DIR] [--json]
 *
 * ## The question, and why it needs its own instrument
 *
 * T-0185 is the one thing `p4_0` — the only picture anyone has of this fort —
 * says about the pickets that the model contradicts: the plate resolves separate
 * posts at a **10 px pitch on a 43 px wall**, 0.23 of the wall's height per post,
 * where the record builds `picket_spacing_m` 0.30 on a 3.7 m wall, **0.081**.
 * Nearly three times finer.
 *
 * `tools/measure_picket_plate.py` answers the first half of that — whether the
 * plate's pitch is a reading of the fort or the floor of its own medium — by
 * measuring what the plate could physically hold. It could not hold this wall:
 * the model's rhythm at the plate's own scale is 2.78 px of post and **0.70 px
 * of gap**, and the narrowest gap that plate draws anywhere on the curtain is
 * 2 px.
 *
 * This file answers the second half, which is a question about the model and not
 * about the plate: **at the distances a visitor stands, does the wall read as
 * posts or as a slab?** A lithograph has ONE viewing distance and a walkable
 * reconstruction has all of them, so the two media cannot be held to one answer —
 * and that asymmetry is only an argument once somebody measures both sides of it
 * in the same unit. The unit is pixels of drawn pitch.
 *
 * ## The method — the SAME statistic, on the other picture
 *
 * `measure_picket_plate.py` reads the plate's rhythm by autocorrelating the
 * curtain's column-mean darkness and by measuring the run lengths of its dark
 * strokes and pale gaps. This file does exactly that to a RENDER of the same
 * wall, from the same stand, so the two readings are the same quantity in the
 * same unit and can be put beside each other. The statistic is restated here in
 * JavaScript rather than shared, because the shot has to be taken in a browser
 * and a ten-line autocorrelation is a smaller cost than a pipe between two
 * runtimes.
 *
 * **Lags under 3 px are excluded and that is not tuning.** Any rendered image is
 * smooth at the pixel scale — multisampling guarantees it — so the correlation of
 * a frame with itself shifted one or two pixels is high whatever is drawn in it.
 * A rhythm is only RESOLVED if it correlates at a lag the eye could separate, so
 * the peak is searched from 3 px up. A wall whose only peak is at 2 px has not
 * failed to be measured: it has stopped reading as posts, which is the finding.
 *
 * Read against two thresholds, both stated before the reading:
 *
 *   * **a peak at 3 px or more, carrying its own harmonic** — a real picket line
 *     correlates again at twice its pitch and a shading gradient does not. That
 *     is what "reads as posts" means here.
 *   * **1 px of gap** — below it the space BETWEEN posts is never a whole pixel
 *     of background and the rhythm survives only as a shade, which is exactly
 *     the bind `p4_0`'s draughtsman was in at 0.70 px.
 *
 * ## The stands, and the rectangles
 *
 * `p4_0`'s own stand is the one `docs/RESEARCH/fort_dearborn_image_accuracy.md`
 * records for the plate comparison — local 1145, 300, yaw 180, on the north bank
 * looking south at the fort. `north_wall` is where a visitor ends up: outside the
 * north curtain by the gate, at the range the sawtooth was built to read at. Both
 * viewports are the release pair, and the phone one is booted with `hasTouch` so
 * it gets the renderer a phone gets rather than a narrow desktop window.
 *
 * The crop rectangles below were read off the shots by eye and are stated rather
 * than buried, the same bargain and for the same reason as the plate constants in
 * `measure_picket_plate.py`. They hold because the stands and the viewports are
 * fixed; the run writes the shot it read beside the number, so a rectangle that
 * has drifted off the wall is visible rather than silent.
 *
 * A reading, not a gate. Nothing here holds a build red; `measure_picket_plate.py
 * --gate` is the ratchet on this stockade and it guards the head, not the rhythm.
 */
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

async function loadPlaywright() {
  let ns;
  try {
    ns = await import('playwright');
  } catch {
    const root = (process.env.NODE_PATH || execSync('npm root -g', { encoding: 'utf8' }))
      .trim().split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, '..');
const argAt = (name) => {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : null;
};
// Defaults to the PUBLISHED mirror for the reason every renderer measurement in
// this project does: the source tree loads uncompressed masters and the site
// loads the compressed derivatives, so a reading off the tree is a reading of
// something no visitor sees.
const WANT_SOURCE = process.argv.includes('--source');
const AS_JSON = process.argv.includes('--json');
const OUT = argAt('--out');
const ROOT = WANT_SOURCE ? APP : path.resolve(APP, '../../site/chicago/4d');
const ENTRY = WANT_SOURCE ? '/renderers/web/' : '/walk/';

// ONE reach per shot, and the reason there is not a pair the way the plate has
// one: a lithograph draws a wall flat and a renderer draws it in perspective, so
// the picket pitch CHIRPS along a rendered curtain and the reach that recedes
// towards the far corner has no single period to find. The reach read here is the
// one nearest parallel to the image plane — the north curtain west of the gate,
// in every shot. `[x0, x1, y0, y1]` in that shot's own pixels, read off by eye and
// stated rather than buried, the same bargain as the plate constants in
// `measure_picket_plate.py`.
const REACHES = {
  'p4_0/desktop': [['north curtain, west of the gate', [200, 430, 399, 414]]],
  'p4_0/phone': [['north curtain, west of the gate', [20, 105, 388, 396]]],
  'north_wall/desktop': [['north curtain, west of the gate', [20, 450, 410, 540]]],
  'north_wall/phone': [['north curtain, west of the gate', [5, 135, 360, 480]]],
};
// `phone-dpr2` frames the IDENTICAL scene as `phone` — same CSS viewport, same
// stand, same camera — on a raster twice as wide. So its rectangle is the phone's
// multiplied by the dsf, which is a derivation and not a second eyeballed
// constant: the wall is in the same place on the glass and only the ruler
// changed. The run writes both shots beside the numbers, so a rectangle that has
// drifted off the wall is still visible rather than silent.
const scaleRect = ([x0, x1, y0, y1], k) => [x0 * k, x1 * k, y0 * k, y1 * k];
const reachesFor = (stand, vpName, dsf) => {
  const own = REACHES[`${stand}/${vpName}`];
  if (own) return own;
  const base = REACHES[`${stand}/phone`];
  if (!base || dsf === 1) return [];
  return base.map(([reach, rect]) => [reach, scaleRect(rect, dsf)]);
};

// The drawn extent of the whole 53 m curtain in that shot, corner to corner, so
// the pitch the wall MUST be drawing can be derived and the pitch that was
// measured can be checked against it. A peak well above the expectation is not a
// finer reading of the wall — it is a moire, the rhythm beating against the pixel
// grid it has fallen under, and it is reported as one.
//
// Only the two `p4_0` shots carry a span: at the north wall the curtain runs out
// of the frame on both sides, so there is no known length to scale by. Nothing is
// lost there, because a 33 px rhythm cannot alias.
const WALL_M = 53;
const SPANS = { 'p4_0/desktop': [157, 950], 'p4_0/phone': [15, 302] };
// Scaled for the same reason and by the same factor: the curtain's two corners
// are at the same place on the glass, counted in a raster dsf times finer.
const spanFor = (stand, vpName, dsf) => {
  const own = SPANS[`${stand}/${vpName}`];
  if (own) return own;
  const base = SPANS[`${stand}/phone`];
  if (!base || dsf === 1) return null;
  return [base[0] * dsf, base[1] * dsf];
};
const ALIAS_FACTOR = 1.5;   // measured this much above expectation is a beat, not a post

const SPACING_M = 0.30;   // form.picket_spacing_m on fort_dearborn_palisade
// hud.js DEFAULTS.quality — the shipped default on BOTH platforms, and the cap in
// `renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, quality))`. Stated
// here so the table can print the backing store each row was actually drawn into;
// if hud.js ever moves it, this becomes a lie and the printed ratio is where it shows.
const QUALITY_DEFAULT = 1.5;
const MIN_LAG = 3;        // below this every rendered image correlates with itself
const MAX_LAG = 60;
const MIN_GAP_PX = 1;     // below this the gap is never a whole pixel of background
const MIN_HARMONIC = 0.15;  // a rhythm repeats at twice its pitch; a gradient does not

const STANDS = [
  ['p4_0', { e: 1145, n: 300, yaw: 180 },
    "the plate's own stand, on the north bank across the river"],
  ['north_wall', { e: 1156.5, n: 253.2, yaw: 180 },
    'outside the north curtain by the gate, where a visitor walks up to it'],
];
/**
 * The viewports, each with the DEVICE PIXEL RATIO it is booted at — and the
 * phone is here twice, because until T-0266 it was only ever read at one of the
 * two ratios a phone can be in.
 *
 * `deviceScaleFactor` is not a detail of the harness. It sets
 * `window.devicePixelRatio` inside the page, and `main.js` boot reads exactly
 * that: `renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1,
 * hud.settings.quality))`, with the shipped default of `quality` **1.5 on both
 * platforms**. So a context at dsf 1 gets `min(1, 1.5)` = **1.0** and a context
 * at dsf 2 gets `min(2, 1.5)` = **1.5**: one backing-store pixel per CSS pixel
 * against three for every two. Every reading this file took before T-0266 was
 * at dsf 1 — which is not what a phone is. It is what a phone becomes when the
 * visitor drops *Render quality* to 1 in Settings, the escape hatch T-0157
 * shipped for frame rate. The default was never measured here at all.
 *
 * dsf 2 rather than 3 because 2 is the floor of the phones this renderer targets
 * and the renderer caps at 1.5 regardless — every phone at dsf 2 or above draws
 * the identical backing store, so 2 stands for all of them and 3 would only
 * enlarge the screenshot.
 *
 * The screenshot comes back at CSS x dsf, and the canvas is composited up to it
 * from the 1.5x backing store — which is what a phone's own compositor does with
 * the same two numbers. So the dsf-2 shot is the picture on the glass, not a
 * proxy for it.
 */
const VIEWPORTS = [
  ['desktop', { width: 1280, height: 800 }, false, 1],
  ['phone', { width: 390, height: 780 }, true, 1],
  ['phone-dpr2', { width: 390, height: 780 }, true, 2],
];

/** Rec. 709 luminance, the same weighting `measure_picket_plate.py` uses. */
const lum = (r, g, b) => 0.2126 * r + 0.7152 * g + 0.0722 * b;

/**
 * The column-mean darkness of one reach — raw, exactly as the plate is read.
 */
function profile(img, [x0, x1, y0, y1]) {
  const { data, width } = img;
  const raw = [];
  for (let x = x0; x < x1; x++) {
    let s = 0;
    for (let y = y0; y < y1; y++) {
      const i = (y * width + x) * 4;
      s += lum(data[i], data[i + 1], data[i + 2]);
    }
    raw.push(s / (y1 - y0));
  }
  return raw;
}

/**
 * The same profile with everything slower than `win` taken out of it.
 *
 * The plate is read raw, because a lithographed wall is evenly lit. A rendered
 * one is not — the sun shades it along its length and the ground behind it
 * changes — and a slow ramp out-correlates the rhythm standing on it at every
 * lag. Subtracting a running mean removes the ramp.
 */
function highpass(raw, win) {
  const h = Math.floor(win / 2);
  return raw.map((v, i) => {
    let s = 0; let n = 0;
    for (let k = Math.max(0, i - h); k <= Math.min(raw.length - 1, i + h); k++) { s += raw[k]; n++; }
    return v - s / n;
  });
}

/**
 * The autocorrelation peak, searched under a filter that provably keeps it.
 *
 * A high-pass wide enough to leave a 33 px rhythm alone is too wide to take the
 * shading off a 4 px one, and one narrow enough for the 4 px rhythm ERASES the
 * 33 px one — so a single window cannot read both a wall across the river and a
 * wall at arm's length. The way out is not to tune the window: it is to refuse
 * to look for a period the window has eaten. Each window is searched only up to
 * `win / 3`, which is inside the band it passes, and the best peak across the
 * ladder wins. A run states the window its reading came from for that reason.
 */
const WINDOWS = [15, 31, 61, 121, 241];

function rhythm(raw) {
  let best = { lag: null, r: -1, window: null, dev: null };
  for (const win of WINDOWS) {
    if (win > raw.length) break;
    const dev = highpass(raw, win);
    const den = dev.reduce((s, v) => s + v * v, 0) || 1;
    const at = (lag) => {
      let s = 0;
      for (let i = 0; i + lag < dev.length; i++) s += dev[i] * dev[i + lag];
      return s / den;
    };
    const hi = Math.min(MAX_LAG, Math.floor(win / 3), Math.floor(raw.length / 3));
    // A LOCAL maximum, never the global one. Whatever is left after a high-pass
    // is still smooth at the shortest lags, so the correlation of a residual with
    // itself shifted three pixels is high even where nothing is periodic — and a
    // global search returns that shoulder every time, which is how this file
    // first reported a 3 px pitch on a wall drawing 35 px posts. A rhythm is a
    // TURNING POINT in the correlation and a shoulder is not, so only turning
    // points are candidates.
    const acf = [];
    for (let l = MIN_LAG - 1; l <= hi + 1; l++) acf[l] = at(l);
    for (let l = MIN_LAG; l <= hi; l++) {
      if (!(acf[l] >= acf[l - 1] && acf[l] >= acf[l + 1])) continue;
      if (acf[l] > best.r) best = { lag: l, r: acf[l], window: win, dev, at };
    }
  }
  if (best.lag === null) return { pitch_px: null, autocorr: 0, harmonic: null, window: null };
  const twice = best.lag * 2;
  const harmonic = twice < Math.floor(best.dev.length / 2) ? best.at(twice) : null;
  return {
    pitch_px: best.lag,
    autocorr: Math.round(best.r * 1000) / 1000,
    harmonic: harmonic === null ? null : Math.round(harmonic * 1000) / 1000,
    window: best.window,
    dev: best.dev,
  };
}

/** Run lengths about the profile's own mean — the drawn post and the drawn gap. */
function strokes(dev) {
  const runs = [];
  let state = null; let n = 0;
  for (const v of dev) {
    const pale = v > 0;
    if (pale === state) n++;
    else { if (state !== null) runs.push([state, n]); state = pale; n = 1; }
  }
  runs.push([state, n]);
  const inner = runs.slice(1, -1);
  const pale = inner.filter(([s]) => s).map(([, k]) => k).sort((x, y) => x - y);
  const dark = inner.filter(([s]) => !s).map(([, k]) => k).sort((x, y) => x - y);
  if (!pale.length || !dark.length) return null;
  const med = (arr) => arr[Math.floor(arr.length / 2)];
  return {
    posts_drawn: dark.length,
    min_stroke_px: dark[0], median_stroke_px: med(dark),
    min_gap_px: pale[0], median_gap_px: med(pale),
  };
}

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.svg': 'image/svg+xml',
  '.geojson': 'application/json', '.webmanifest': 'application/manifest+json',
};
const server = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  let file = path.join(ROOT, decodeURIComponent(url.pathname));
  try {
    if (file.endsWith('/')) file = path.join(file, 'index.html');
    const body = await readFile(file);
    res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
    res.end(body);
  } catch { res.writeHead(404).end('nope'); }
});
await new Promise((r) => server.listen(0, r));
const base = `http://127.0.0.1:${server.address().port}`;

/**
 * The reading, taken inside the page.
 *
 * The apex ring is the honest sample: four vertices at exactly one height per
 * post, which is what makes "neighbouring posts" a thing that can be counted
 * without knowing how the archetype orders its buffer. Posts are collapsed to
 * their own mean position, dropped unless they face the camera (a wall the
 * visitor cannot see contributes nothing to what the wall reads as) and unless
 * they are in front of the near plane, then sorted along the screen and read as
 * consecutive differences. The MEDIAN, because the run turns two corners and a
 * corner pair is not a pitch.
 */
const rows = [];
const errors = [];
const shots = [];
for (const [vpName, viewport, hasTouch, dsf] of VIEWPORTS) {
  const browser = await chromium.launch({
    executablePath: process.env.PW_EXECUTABLE || undefined,
    args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'],
  });
  const ctx = await browser.newContext({ viewport, hasTouch, deviceScaleFactor: dsf });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => errors.push(`${vpName}: ${e}`));
  await page.addInitScript(() => {
    localStorage.setItem('chicago4d.detail', 'full');
    localStorage.setItem('chicago4d.entered', '1');
  });
  page.setDefaultTimeout(180000);
  await page.goto(`${base}${ENTRY}?year=1835`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 180000 });
  const gate = await page.$('#gate button, .gate button');
  if (gate) { await gate.click(); await page.waitForTimeout(1200); }
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      if (/got it/i.test(b.textContent ?? '')) b.click();
    }
  });

  for (const [standName, at, why] of STANDS) {
    await page.evaluate((t) => {
      window.__chicago4d.setFly(false);
      window.__chicago4d.walker.teleport(t);
    }, { local_e: at.e, local_n: at.n, yaw_deg: at.yaw });
    await page.waitForTimeout(900);
    const name = `t-0185-${standName}-${vpName}.png`;
    const file = OUT ? path.join(OUT, name) : null;
    if (file) await mkdir(OUT, { recursive: true });
    const png = await page.screenshot(file ? { path: file } : {});
    shots.push({ key: `${standName}/${vpName}`, stand: standName, viewport: vpName, dsf, why, name, png });
  }
  await browser.close();
}
server.close();

// ---- read the shots ------------------------------------------------------ //
//
// Decoding a PNG without a dependency: Chromium is already here, so the pixels
// come back through a canvas in a blank page rather than through a decoder this
// repository would then have to own.
const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'],
});
const page = await browser.newPage();
await page.goto('about:blank');
for (const shot of shots) {
  const reaches = reachesFor(shot.stand, shot.viewport, shot.dsf);
  const img = await page.evaluate(async (b64) => {
    const blob = await (await fetch(`data:image/png;base64,${b64}`)).blob();
    const bmp = await createImageBitmap(blob);
    const c = new OffscreenCanvas(bmp.width, bmp.height);
    const g = c.getContext('2d');
    g.drawImage(bmp, 0, 0);
    const d = g.getImageData(0, 0, bmp.width, bmp.height);
    return { width: bmp.width, height: bmp.height, data: Array.from(d.data) };
  }, shot.png.toString('base64'));
  for (const [reach, rect] of reaches) {
    const raw = profile(img, rect);
    const { dev, ...read } = rhythm(raw);
    const sp = spanFor(shot.stand, shot.viewport, shot.dsf);
    const pxPerM = sp ? (sp[1] - sp[0]) / WALL_M : null;
    rows.push({
      stand: shot.stand, viewport: shot.viewport, dsf: shot.dsf,
      pixel_ratio: Math.min(shot.dsf, QUALITY_DEFAULT),
      reach, rect, shot: shot.name, why: shot.why,
      px_per_m: pxPerM ? Math.round(pxPerM * 100) / 100 : null,
      expected_px: pxPerM ? Math.round(SPACING_M * pxPerM * 100) / 100 : null,
      ...read, strokes: dev ? strokes(dev) : null,
    });
  }
}
await browser.close();

const verdict = (r) => {
  if (!r.pitch_px || r.autocorr < 0.2) return 'A SLAB — no rhythm at 3 px or more';
  if (r.harmonic === null || r.harmonic < MIN_HARMONIC) return 'unresolved — peak carries no harmonic';
  if (r.expected_px && r.pitch_px > r.expected_px * ALIAS_FACTOR) {
    return `ALIASED — beats at ${r.pitch_px} px on a ${r.expected_px} px wall`;
  }
  if (r.strokes && r.strokes.min_gap_px < MIN_GAP_PX) return 'posts, gap sub-pixel';
  return 'POSTS';
};

if (AS_JSON) {
  console.log(JSON.stringify({ rows, errors }, null, 1));
} else {
  console.log('\n  THE MODEL ON SCREEN — the drawn picket rhythm where a visitor stands');
  console.log(`    source: ${WANT_SOURCE ? 'the working tree' : 'the published mirror'}`);
  console.log('    stand       viewport     dpr  ratio  measured  expected  autocorr    2x   win   reads as');
  for (const r of rows) {
    console.log(`    ${r.stand.padEnd(11)} ${r.viewport.padEnd(11)} `
      + `${String(r.dsf).padStart(3)}  ${r.pixel_ratio.toFixed(1).padStart(4)}x `
      + `${String(r.pitch_px ?? '—').padStart(5)} px ${(r.expected_px ? `${r.expected_px} px` : '—').padStart(9)} `
      + `${r.autocorr.toFixed(2).padStart(8)} ${(r.harmonic === null ? '—' : r.harmonic.toFixed(2)).padStart(5)} `
      + `${String(r.window ?? '—').padStart(4)}   ${verdict(r)}`);
  }
  console.log(`    thresholds: a peak at ${MIN_LAG} px or more carrying a harmonic of at least `
    + `${MIN_HARMONIC}, and ${MIN_GAP_PX} px of gap for the gap itself to be drawn`);
  console.log('    the plate, for comparison: 10 px pitch, autocorr +0.69, gaps 2-5 px — '
    + 'and it could not have drawn the model\'s 0.70 px gap (measure_picket_plate.py)');
  console.log(`    dpr is the context's devicePixelRatio and ratio is what the renderer then asks `
    + `for, min(dpr, quality ${QUALITY_DEFAULT}); the phone rows are the SAME device at the two `
    + `settings — dpr 1 is Render quality 1, the escape hatch, and dpr 2 is the shipped default`);
  if (errors.length) console.log(`    pageerrors: ${errors.length}`);
}
process.exit(errors.length ? 1 : 0);
