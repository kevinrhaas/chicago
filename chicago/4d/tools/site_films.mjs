/**
 * site_films.mjs — film the public site's feature films from the app itself.
 *
 *   node tools/site_films.mjs --year 1904 --ctl DIR [--view 1280x720] [--detail full] [--gpu] [--headed]
 *
 * --gpu draws on the machine's own graphics card instead of SwiftShader (a Mac's Metal
 * GPU draws a 1904 frame in well under a second, against ~25 s in software); --headed
 * opens a visible window, which some GPUs need. PW_CHANNEL=chrome uses installed Chrome.
 *
 * The public site (site/, chicago.polecat.live) shows the app's features as short
 * cinematic films: people coming and going, horse teams, boats, seasons, jaunts. Every
 * frame is drawn by the app. Booting a year under SwiftShader takes from one minute
 * (1812) to many (1904), so this tool boots ONE year and then serves a queue: drop a
 * job file into DIR/queue/ and its answer appears in DIR/done/. That way one boot can be
 * explored (where is the Pullman carriage now?), framed (stills) and filmed.
 *
 * Jobs (JSON):
 *   { "type": "eval",  "js": "return api.season.current" }        any page code; `api` is window.__chicago4d
 *   { "type": "still", "pose": {...}, "out": "x.jpg", "ui": false } one frame (ui: true keeps the HUD, slow)
 *   { "type": "film",  "id": "...", "seconds": 8, "fps": 24, "setup": "js", "keys": [...] | "track": {...} }
 *   { "type": "quit" }
 *
 * A pose is { e, n, alt, yaw, pitch } or { e, n, alt, look: [e, n, h] }. `keys` are poses
 * with a `t` in [0, 1], eased between (smoothstep per segment, yaw the short way round).
 * `track` follows something that moves: `track.js` returns { e, n, heading } each frame
 * (heading in degrees, clockwise from north), and the camera sits at `track.offset`
 * ({ back, side, alt }) in that frame, looking at it (`track.look_h` above its ground),
 * optionally swinging round it by `track.swing` degrees over the film.
 *
 * Time is virtual while filming: performance.now() advances exactly 1/fps per frame, so
 * people, horses and water move at their true speed whatever the frame costs to draw.
 */
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import fs from 'node:fs';
import path from 'node:path';
import { execSync, execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

async function loadPlaywright() {
  let ns;
  try { ns = await import('playwright'); } catch {
    const root = (process.env.NODE_PATH || execSync('npm root -g', { encoding: 'utf8' })).trim().split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, '..');
// --site films the PUBLISHED mirror (site/4d, after tools/publish.sh), which carries the
// large GLBs publish materialises (Glessner) and the compiled cards; the source tree does not.
const SITE = process.argv.includes('--site') ? path.resolve(APP, '../../site/4d') : null;
const ROOT = SITE ?? APP;
const ENTRY = SITE ? '/walk/index.html' : '/renderers/web/index.html';
const argv = process.argv.slice(2);
const value = (name, fallback) => { const i = argv.indexOf(name); return i > -1 && argv[i + 1] ? argv[i + 1] : fallback; };
const YEAR = value('--year', '1904');
const CTL = path.resolve(value('--ctl', `/tmp/site-films-${YEAR}`));
const DETAIL = value('--detail', 'full');
const [VW, VH] = value('--view', '1280x720').split('x').map(Number);
for (const d of ['queue', 'done', 'frames', 'out']) fs.mkdirSync(path.join(CTL, d), { recursive: true });
const log = (...a) => { const line = `[${new Date().toISOString().slice(11, 19)}] ${a.join(' ')}`; console.log(line); fs.appendFileSync(path.join(CTL, 'log.txt'), line + '\n'); };

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.glb': 'model/gltf-binary', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.ktx2': 'image/ktx2', '.webp': 'image/webp', '.wasm': 'application/wasm',
  '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.mp4': 'video/mp4', '.webm': 'video/webm' };
const server = createServer(async (req, res) => {
  let file = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  try {
    if ((await stat(file)).isDirectory()) file = path.join(file, 'index.html');
    const body = await readFile(file);
    res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
    res.end(body);
  } catch { res.writeHead(404).end('nope'); }
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}`;

const { chromium } = await loadPlaywright();
const GPU = argv.includes('--gpu');
const GL_ARGS = GPU
  ? ['--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--enable-zero-copy', ...(process.platform === 'darwin' ? ['--use-angle=metal'] : [])]
  : ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  channel: process.env.PW_CHANNEL || undefined, headless: !argv.includes('--headed'), args: GL_ARGS });
const page = await browser.newPage({ viewport: { width: VW, height: VH }, deviceScaleFactor: 1 });
page.setDefaultTimeout(1_800_000);
const errors = [];
page.on('pageerror', e => { errors.push(String(e)); log('pageerror', String(e).slice(0, 200)); });
await page.addInitScript((d) => {
  localStorage.setItem('chicago4d.detail', d);
  localStorage.setItem('chicago4d.entered', '1');
  localStorage.setItem('chicago4d.help.seen', '1');
  const s = JSON.parse(localStorage.getItem('chicago4d.settings') || '{}');
  s.detail = d; s.quality = 'high';
  localStorage.setItem('chicago4d.settings', JSON.stringify(s));
  // The virtual clock: real time until a film freezes it, then exactly what advance() gives.
  const realNow = performance.now.bind(performance);
  let frozen = null, offset = 0;
  performance.now = () => (frozen ?? realNow() + offset);
  window.__film = {
    freeze() { frozen = realNow() + offset; },
    advance(ms) { frozen += ms; },
    release() { if (frozen != null) { offset = frozen - realNow(); frozen = null; } },
  };
}, DETAIL);

const t0 = Date.now();
await page.goto(`${base}${ENTRY}?year=${YEAR}`, { waitUntil: 'domcontentloaded' });
try {
  await page.waitForFunction(() => window.__chicago4d?.ready === true || window.__chicago4d?.error, null, { timeout: 1_800_000, polling: 2000 });
} catch {}
const bootErr = await page.evaluate(() => window.__chicago4d?.error);
if (bootErr) { log(`boot failed: ${bootErr}`); process.exit(1); }
log(`${YEAR}: ready in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
await page.evaluate(async () => {
  const api = window.__chicago4d;
  for (let i = 0; i < 40 && api.welcome?.state !== 'world'; i++) { try { api.welcome?.enter?.('spawn'); } catch {} await new Promise(r => setTimeout(r, 500)); }
  document.exitPointerLock?.();
  for (const b of document.querySelectorAll('button')) if (/got it|dismiss/i.test(b.textContent ?? '')) b.click();
  const style = document.createElement('style');
  style.id = '__film-hide';
  style.textContent = 'body > *:not(#view):not(canvas) { visibility: hidden !important; }';
  document.head.append(style);
  api.renderer.setAnimationLoop(null);
});
log(`${YEAR}: in the town (${await page.evaluate(() => window.__chicago4d.welcome?.state)})`);
fs.writeFileSync(path.join(CTL, 'ready'), String(Date.now()));

// ---- camera maths ------------------------------------------------------------------
const lerp = (a, b, s) => a + (b - a) * s;
const ease = s => s * s * (3 - 2 * s);
const yawLerp = (a, b, s) => { let d = ((b - a + 540) % 360) - 180; return (a + d * s + 360) % 360; };
function solve(p) {
  // A pose with `look` gets its yaw and pitch from the point it looks at.
  if (!p.look) return { ...p };
  const [le, ln, lh] = p.look; const de = le - p.e, dn = ln - p.n;
  const yaw = (Math.atan2(de, dn) * 180 / Math.PI + 360) % 360;
  const pitch = Math.atan2((lh ?? 0) - (p.alt ?? 1.6), Math.hypot(de, dn)) * 180 / Math.PI;
  return { ...p, yaw, pitch };
}
function keyPose(keys, t) {
  const ks = keys.map(solve);
  if (t <= ks[0].t) return ks[0];
  for (let i = 0; i < ks.length - 1; i++) {
    const a = ks[i], b = ks[i + 1];
    if (t <= b.t) {
      const s = ease((t - a.t) / (b.t - a.t || 1));
      return { e: lerp(a.e, b.e, s), n: lerp(a.n, b.n, s), alt: lerp(a.alt, b.alt, s), yaw: yawLerp(a.yaw, b.yaw, s), pitch: lerp(a.pitch, b.pitch, s) };
    }
  }
  return ks[ks.length - 1];
}
// A cinematic path: `"path": "spline"` runs the camera through every key on one Catmull-Rom
// curve (position and look point alike) at an even pace, easing only at the very start and
// end (`ease_ends`, a fraction of the film, default 0.15; 0 for a film that loops). The
// smoothstep path above stops at every key, which reads as a robot arm, not a crane.
const cr = (p0, p1, p2, p3, s) => 0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (-p0 + 3 * p1 - 3 * p2 + p3) * s * s * s);
function splinePose(keys, u, easeEnds = 0.15) {
  const k = easeEnds > 0 ? (() => {
    // Even pace in the middle, a smooth start and stop over easeEnds at each end.
    const a = Math.min(0.49, easeEnds), v = 1 / (1 - a);
    if (u < a) return v * u * u / (2 * a);
    if (u > 1 - a) { const r = 1 - u; return 1 - v * r * r / (2 * a); }
    return v * (u - a / 2);
  })() : u;
  const pts = keys.map(p => {
    const look = p.look ?? (() => { const y = (p.yaw ?? 0) * Math.PI / 180, pi = (p.pitch ?? 0) * Math.PI / 180;
      return [p.e + Math.sin(y) * 100 * Math.cos(pi), p.n + Math.cos(y) * 100 * Math.cos(pi), (p.alt ?? 1.6) + Math.sin(pi) * 100]; })();
    return [p.e, p.n, p.alt ?? 1.6, look[0], look[1], look[2] ?? 0];
  });
  const m = pts.length - 1, x = Math.max(0, Math.min(1, k)) * m, i = Math.min(m - 1, Math.floor(x)), s = x - i;
  const P = j => pts[Math.max(0, Math.min(m, j))];
  const q = P(i).map((_, d) => cr(P(i - 1)[d], P(i)[d], P(i + 1)[d], P(i + 2)[d], s));
  return solve({ e: q[0], n: q[1], alt: q[2], look: [q[3], q[4], q[5]] });
}
const posePath = (job, u) => (job.path === 'spline' ? splinePose(job.keys, u, job.ease_ends ?? 0.15) : keyPose(job.keys, u));
const toTeleport = p => ({ local_e: p.e, local_n: p.n, yaw_deg: p.yaw, pitch_deg: p.pitch, altitude_m: p.alt });

async function frame(pose, steps, ms) {
  return page.evaluate(({ pose, steps, ms }) => {
    const api = window.__chicago4d;
    api.setFly(typeof pose.altitude_m === 'number');
    api.walker.teleport(pose);
    for (let i = 0; i < steps; i++) { if (ms) window.__film.advance(ms / steps); api.step(); }
    return api.renderer.domElement.toDataURL('image/jpeg', 0.95);
  }, { pose, steps, ms });
}
// A tracked pose is worked out in the page, where the moving thing is.
async function trackFrame(track, u, steps, ms) {
  return page.evaluate(({ track, u, steps, ms }) => {
    const api = window.__chicago4d;
    for (let i = 0; i < steps; i++) { if (ms) window.__film.advance(ms / steps); if (i < steps - 1) api.step(); }
    const at = new Function('api', track.js)(api);
    if (!at) return null;
    const o = track.offset ?? { back: 8, side: 2, alt: 2.5 };
    const h = ((at.heading ?? 0) + (track.swing ?? 0) * (u - 0.5) + (track.turn ?? 0)) * Math.PI / 180;
    // Behind (back) and to the right (side) of the heading.
    const fe = Math.sin(h), fn = Math.cos(h);
    const e = at.e - fe * o.back + fn * (o.side ?? 0), n = at.n - fn * o.back - fe * (o.side ?? 0);
    const de = at.e + fe * (track.lead ?? 0) - e, dn = at.n + fn * (track.lead ?? 0) - n;
    const yaw = (Math.atan2(de, dn) * 180 / Math.PI + 360) % 360;
    const pitch = Math.atan2((track.look_h ?? 1.5) - o.alt, Math.hypot(de, dn)) * 180 / Math.PI;
    api.setFly(true);
    api.walker.teleport({ local_e: e, local_n: n, yaw_deg: yaw, pitch_deg: pitch, altitude_m: o.alt });
    api.step();
    return api.renderer.domElement.toDataURL('image/jpeg', 0.95);
  }, { track, u, steps, ms });
}

// The visitor's own eye, wherever the town has put it (in a boat, on a carriage seat, on a jaunt).
// `pov.js`, if given, runs before each frame with (api, u) — to turn the head, say.
async function povFrame(steps, ms, pov = {}, u = 0) {
  return page.evaluate(({ steps, ms, js, u }) => {
    const api = window.__chicago4d;
    for (let i = 0; i < steps; i++) { if (ms) window.__film.advance(ms / steps); if (js) new Function('api', 'u', js)(api, u); api.step(); }
    return api.renderer.domElement.toDataURL('image/jpeg', 0.95);
  }, { steps, ms, js: pov.js ?? null, u });
}

function encode(dir, outStem, fps, crf = 26) {
  const vf = `scale=${VW}:${VH}:flags=lanczos`;
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(fps), '-i', path.join(dir, '%04d.jpg'), '-vf', vf, '-an',
    '-c:v', 'libx264', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-crf', String(crf), '-preset', 'slow', '-movflags', '+faststart', `${outStem}.mp4`]);
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', path.join(dir, '0000.jpg'), '-vf', vf, '-q:v', '4', `${outStem}.jpg`]);
  return fs.statSync(`${outStem}.mp4`).size;
}
const save = (file, dataUrl) => fs.writeFileSync(file, Buffer.from(dataUrl.split(',')[1], 'base64'));

async function run(job) {
  if (job.type === 'eval') {
    return page.evaluate(async (js) => { const api = window.__chicago4d; return await (new Function('api', `return (async () => { ${js} })()`))(api); }, job.js);
  }
  if (job.type === 'step') {
    // Let the town run in real time for a while (people walk on, teams go round).
    return page.evaluate(async ({ seconds }) => { const api = window.__chicago4d; const end = performance.now() + seconds * 1000;
      let n = 0; while (performance.now() < end) { api.step(); n++; await new Promise(r => setTimeout(r, 0)); } return n; }, { seconds: job.seconds ?? 10 });
  }
  if (job.type === 'still') {
    if (job.setup) await run({ type: 'eval', js: job.setup });
    const pose = toTeleport(solve(job.pose));
    if (job.ui) {
      await page.evaluate((pose) => { const api = window.__chicago4d; document.getElementById('__film-hide')?.remove();
        api.setFly(typeof pose.altitude_m === 'number'); api.walker.teleport(pose); for (let i = 0; i < 4; i++) api.step(); }, pose);
      await page.screenshot({ path: path.resolve(CTL, 'out', job.out), type: 'jpeg', quality: 90 });
      await page.evaluate(() => { const s = document.createElement('style'); s.id = '__film-hide';
        s.textContent = 'body > *:not(#view):not(canvas) { visibility: hidden !important; }'; document.head.append(s); });
    } else {
      save(path.resolve(CTL, 'out', job.out), await frame(pose, job.steps ?? 4, 0));
    }
    return job.out;
  }
  if (job.type === 'film') {
    if (job.setup) log(`${job.id}: setup → ${JSON.stringify(await run({ type: 'eval', js: job.setup })).slice(0, 200)}`);
    const fps = job.fps ?? 24, n = Math.round((job.seconds ?? 8) * fps);
    const dir = path.join(CTL, 'frames', job.id);
    fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
    await page.evaluate(() => window.__film.freeze());
    const started = Date.now();
    // Settle: a few still frames at the first pose so streamed detail has arrived.
    const p0 = job.track || job.pov ? null : toTeleport(posePath(job, 0));
    for (let k = 0; k < (job.settle ?? 6); k++) {
      if (p0) await frame(p0, 1, 0); else if (job.track) await trackFrame(job.track, 0, 1, 0); else await povFrame(1, 0);
    }
    if (job.start) log(`${job.id}: start → ${JSON.stringify(await run({ type: 'eval', js: job.start })).slice(0, 200)}`);
    const step = job.steps ?? 1;
    for (let k = 0; k < n; k++) {
      const u = n > 1 ? k / (n - 1) : 0;
      const ms = 1000 / fps;
      const img = job.track ? await trackFrame(job.track, u, step, ms) : job.pov ? await povFrame(step, ms, job.pov, u)
        : await frame(toTeleport(posePath(job, u)), step, ms);
      if (!img) throw new Error(`${job.id}: nothing to track at frame ${k}`);
      save(path.join(dir, `${String(k).padStart(4, '0')}.jpg`), img);
      if (k % 24 === 0) log(`${job.id}: frame ${k}/${n} after ${((Date.now() - started) / 1000).toFixed(0)} s`);
    }
    await page.evaluate(() => window.__film.release());
    const bytes = encode(dir, path.join(CTL, 'out', job.id), fps, job.crf ?? 26);
    return { id: job.id, frames: n, seconds: (Date.now() - started) / 1000, bytes };
  }
  if (job.type === 'quit') return 'bye';
  throw new Error(`unknown job type ${job.type}`);
}

for (;;) {
  const files = fs.readdirSync(path.join(CTL, 'queue')).filter(f => f.endsWith('.json')).sort();
  if (!files.length) { await new Promise(r => setTimeout(r, 1000)); continue; }
  const name = files[0], src = path.join(CTL, 'queue', name);
  let job; try { job = JSON.parse(fs.readFileSync(src, 'utf8')); } catch (e) { fs.renameSync(src, path.join(CTL, 'done', name + '.bad')); continue; }
  fs.rmSync(src);
  const t = Date.now();
  let result, error = null;
  try { result = await run(job); } catch (e) { error = String(e?.stack ?? e).slice(0, 2000); }
  fs.writeFileSync(path.join(CTL, 'done', name), JSON.stringify({ job: job.type, ms: Date.now() - t, result, error }, null, 1));
  log(`${name}: ${error ? 'ERROR ' + error.slice(0, 160) : 'ok'} (${((Date.now() - t) / 1000).toFixed(1)} s)`);
  if (job.type === 'quit') break;
}
await browser.close();
server.close();
process.exit(0);
