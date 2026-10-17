/**
 * portal_clips.mjs — film the home page's destination clips from the app itself (T-2685).
 *
 *   node tools/portal_clips.mjs --year 1835                 every shot of one year
 *   node tools/portal_clips.mjs --year 1904 --shots a,b     a subset, while iterating
 *   node tools/portal_clips.mjs --year 1812 --stills        one frame per shot (t = 0, .25, .5)
 *                                                           to judge a framing before filming it
 *   node tools/portal_clips.mjs ... --frames 80 --fps 10    defaults: 80 frames at 10 fps (8 s)
 *   node tools/portal_clips.mjs ... --out DIR               PNG frames (default /tmp/portal-clips)
 *
 * The owner, 2026-10-16: the three destination cards on the home page should show a
 * moving image from each year, picked at random per load from a small library, each one a
 * seamless loop. So every shot in `tools/portal_clips/<year>.json` is a camera move that is
 * a function of t in [0, 1) and returns to its first pose at t = 1: a full orbit, or a
 * swing, pan or drift that follows a sine. Frame k is t = k / frames, so the last frame
 * is one step short of the first and the loop has no repeated frame and no seam.
 *
 * It drives the scene the way `critic_shots.mjs` and `shoot.mjs` do — `walker.teleport`,
 * `setFly`, `setAnimationHold`, `capture` — and adds no hook to the renderer. The clock is
 * held, so wind and water stand still and the first and last frames match exactly.
 * Output is 480x160, no audio, as H.264 MP4 and VP9 WebM, written to
 * renderers/web/portal/clips/<year>-<shot>.{mp4,webm} (published as walk/portal/clips/).
 * `--encode` re-encodes from the frames already on disk.
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
const argv = process.argv.slice(2);
const flag = (name) => argv.includes(name);
const value = (name, fallback) => { const i = argv.indexOf(name); return i > -1 && argv[i + 1] ? argv[i + 1] : fallback; };

const YEAR = value('--year', '');
// One shot list per year, so three years can be planned and filmed side by side.
const PLAN_FILE = path.join(HERE, 'portal_clips', `${YEAR}.json`);
if (!/^\d{4}$/.test(YEAR) || !fs.existsSync(PLAN_FILE)) { console.error(`--year: no shot list at ${path.relative(APP, PLAN_FILE)}`); process.exit(2); }
const PLAN = { frames: 80, fps: 10, size: '480x160', crf: 30, ...JSON.parse(fs.readFileSync(PLAN_FILE, 'utf8')) };
const PICK = value('--shots', '').split(',').filter(Boolean);
const SHOTS = PLAN.shots.filter(s => !PICK.length || PICK.includes(s.id));
const STILLS = flag('--stills');
const FRAMES = Number(value('--frames', PLAN.frames ?? 96));
const FPS = Number(value('--fps', PLAN.fps ?? 12));
const OUT = path.resolve(value('--out', '/tmp/portal-clips'));
const CLIPS = path.join(APP, 'renderers/web/portal/clips');
const DETAIL = value('--detail', 'balanced');
// Filmed at twice the clip size and scaled down, so the clip is low-resolution on
// purpose rather than aliased by accident.
const [VW, VH] = value('--view', '720x240').split('x').map(Number);
const VIEW = { width: VW, height: VH };
const SIZE = PLAN.size ?? '480x160';

/** A parameter is a number or a sine: {base, amp, phase?, cycles?}. */
function wave(p, t) {
  if (typeof p === 'number' || p == null) return p;
  return p.base + (p.amp ?? 0) * Math.sin(2 * Math.PI * ((p.cycles ?? 1) * t + (p.phase ?? 0)));
}
/** The pose at t for one shot. Every form returns to its first pose at t = 1. */
function poseAt(shot, t) {
  if (shot.orbit) {
    const o = shot.orbit;
    const bearing = o.turn ? o.bearing + o.turn * t : wave({ base: o.bearing, amp: o.swing ?? 0 }, t);
    const radius = wave(o.radius, t), alt = wave(o.alt, t);
    const b = bearing * Math.PI / 180;
    const e = o.center[0] - radius * Math.sin(b), n = o.center[1] - radius * Math.cos(b);
    // Aim at a point `look_y` above the centre's ground, unless a pitch is given.
    const pitch = o.pitch != null ? wave(o.pitch, t) : -Math.atan2(alt - (o.look_y ?? 0), radius) * 180 / Math.PI;
    return { local_e: e, local_n: n, yaw_deg: ((bearing % 360) + 360) % 360, altitude_m: alt, pitch_deg: pitch };
  }
  const p = shot.pose;
  const out = { local_e: wave(p.e, t), local_n: wave(p.n, t), yaw_deg: wave(p.yaw, t), pitch_deg: wave(p.pitch ?? 0, t) };
  if (p.alt != null) out.altitude_m = wave(p.alt, t);
  // A drift: slide between two points and back, eased so the turn-round has no jolt.
  if (p.from && p.to) {
    const s = (1 - Math.cos(2 * Math.PI * t)) / 2;
    out.local_e = p.from[0] + (p.to[0] - p.from[0]) * s;
    out.local_n = p.from[1] + (p.to[1] - p.from[1]) * s;
  }
  return out;
}

/**
 * Two encodings of the same frames, and the page fetches one: VP9 WebM where the browser
 * plays it (Chrome, Firefox, Edge — and the Chromium the smoke test drives, which has no
 * H.264), H.264 MP4 otherwise (Safari, every iPhone browser).
 */
function encode(shot) {
  const dir = path.join(OUT, YEAR, shot.id);
  if (!fs.existsSync(path.join(dir, '0000.png'))) throw new Error(`${shot.id}: no frames in ${dir}`);
  fs.mkdirSync(CLIPS, { recursive: true });
  const stem = path.join(CLIPS, `${YEAR}-${shot.id}`);
  const scale = `scale=${SIZE.replace('x', ':')}:flags=area`;
  const input = ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(dir, '%04d.png'), '-vf', scale, '-an'];
  execFileSync('ffmpeg', [...input, '-c:v', 'libx264', '-profile:v', 'baseline', '-level', '3.0', '-pix_fmt', 'yuv420p',
    '-crf', String(PLAN.crf ?? 30), '-preset', 'veryslow', '-g', String(FRAMES), '-movflags', '+faststart', `${stem}.mp4`]);
  execFileSync('ffmpeg', [...input, '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuv420p', '-b:v', '0', '-crf', String((PLAN.crf ?? 30) + 12),
    '-row-mt', '1', '-deadline', 'good', '-cpu-used', '1', '-g', String(FRAMES), `${stem}.webm`]);
  return ['mp4', 'webm'].map(x => `${path.relative(APP, stem)}.${x} ${(fs.statSync(`${stem}.${x}`).size / 1024).toFixed(0)} KB`).join(', ');
}
// `--encode` re-encodes shots already filmed, from the frames on disk, without a browser.
if (flag('--encode')) {
  for (const shot of SHOTS) console.log(`${YEAR}/${shot.id}: ${encode(shot)}`);
  process.exit(0);
}

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.glb': 'model/gltf-binary', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.ktx2': 'image/ktx2', '.webp': 'image/webp', '.wasm': 'application/wasm' };
const server = createServer(async (req, res) => {
  let file = path.join(APP, decodeURIComponent(new URL(req.url, 'http://x').pathname));
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
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: VIEW, deviceScaleFactor: 1 });
page.setDefaultTimeout(300_000);
const errors = [];
page.on('pageerror', e => errors.push(String(e)));
await page.addInitScript((d) => {
  localStorage.setItem('chicago4d.detail', d);
  localStorage.setItem('chicago4d.entered', '1');
  localStorage.setItem('chicago4d.help.seen', '1');
  const s = JSON.parse(localStorage.getItem('chicago4d.settings') || '{}');
  s.detail = d; s.quality = 'high';
  localStorage.setItem('chicago4d.settings', JSON.stringify(s));
}, DETAIL);
const t0 = Date.now();
await page.goto(`${base}/renderers/web/index.html?year=${YEAR}`, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => {
  const api = window.__chicago4d;
  if (typeof api?.setAnimationHold !== 'function') return false;
  api.setAnimationHold(true); return true;
}, null, { polling: 'raf' });
const progress = setInterval(async () => {
  const st = await page.evaluate(() => ({ ready: window.__chicago4d?.ready, gate: document.getElementById('gate-sub')?.textContent?.slice(0, 80) })).catch(() => null);
  if (process.env.CLIPS_VERBOSE) console.log(`  boot ${((Date.now() - t0) / 1000).toFixed(0)} s: ${JSON.stringify(st)}`);
}, 20_000);
try {
  await page.waitForFunction(() => window.__chicago4d?.ready === true || window.__chicago4d?.error, null, { timeout: 900_000 });
} catch {}
clearInterval(progress);
const bootErr = await page.evaluate(() => window.__chicago4d?.error);
if (bootErr) { console.error(`boot failed: ${bootErr}\n${errors.join('\n')}`); process.exit(1); }
console.log(`${YEAR}: ready in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
// Enter the town: the welcome gate's button, pressed from the page so a disabled or
// animating button cannot stall the run on Playwright's actionability wait.
await page.evaluate(() => document.getElementById('gate-btn')?.click());
await page.waitForTimeout(1500);
await page.evaluate(() => {
  for (const b of document.querySelectorAll('button')) if (/got it|dismiss|close/i.test(b.textContent ?? '')) b.click();
  const style = document.createElement('style');
  style.textContent = 'body > *:not(#view) { visibility: hidden !important; }';
  document.head.append(style);
  // The page's own loop stops: every frame is drawn by `step()` below, and a loop
  // drawing in between would double the cost of each one under SwiftShader.
  window.__chicago4d.renderer.setAnimationLoop(null);
});
const canvas = (await page.$('#view')) ?? (await page.$('canvas'));

for (const shot of SHOTS) {
  const dir = path.join(OUT, YEAR, shot.id);
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  const ts = STILLS ? [0, 0.25, 0.5] : Array.from({ length: FRAMES }, (_, k) => k / FRAMES);
  const started = Date.now();
  for (let k = 0; k < ts.length; k++) {
    const pose = poseAt(shot, ts[k]);
    // `step()` runs one whole tick with the flora given no time budget, so every
    // camera-driven layer finishes its rebuild in that tick, and draws it; the
    // drawing buffer is read in the same task, before the browser composites and
    // clears it. One draw per frame — a Playwright screenshot of a WebGL canvas
    // under SwiftShader cost about 80 s.
    const png = await page.evaluate(({ pose, steps }) => {
      const api = window.__chicago4d;
      api.setFly(typeof pose.altitude_m === 'number');
      api.walker.teleport(pose);
      for (let i = 0; i < steps; i++) api.step();
      return api.renderer.domElement.toDataURL('image/png');
    }, { pose, steps: k === 0 ? 4 : (shot.steps ?? 1) });
    fs.writeFileSync(path.join(dir, `${String(k).padStart(4, '0')}.png`), Buffer.from(png.split(',')[1], 'base64'));
    if (process.env.CLIPS_VERBOSE && k % 8 === 0) console.log(`  ${shot.id} frame ${k}: ${((Date.now() - started) / 1000).toFixed(0)} s`);
  }
  const secs = (Date.now() - started) / 1000;
  if (STILLS) {
    // One contact sheet per shot, the three stills stacked.
    const sheet = path.join(OUT, YEAR, `${shot.id}-stills.jpg`);
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', path.join(dir, '%04d.png'), '-vf', 'scale=480:-1,tile=1x3', '-frames:v', '1', sheet]);
    console.log(`${YEAR}/${shot.id}: stills → ${sheet} (${secs.toFixed(0)} s)`);
    continue;
  }
  const sizes = encode(shot);
  console.log(`${YEAR}/${shot.id}: ${ts.length} frames in ${secs.toFixed(0)} s → ${sizes}`);
}
if (errors.length) console.log(`page errors:\n${errors.slice(0, 10).join('\n')}`);
await browser.close();
server.close();
process.exit(0);
