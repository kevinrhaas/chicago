/**
 * sv_film.mjs — film the Today window (Google Street View beside the 1904 town) in use, in real
 * time, from the deployed dev preview (T-3744; Kevin 2026-11-24: "a video with the actual google
 * street view picker shown and navigating, starting at the Glessner House corner").
 *
 *   PW_CHANNEL=chrome node sv_film.mjs --out DIR [--url URL] [--view 1600x900] [--settle 25]
 *
 * The Today window only draws Street View on the hosts its key is restricted to, so this films
 * the real dev preview (a webdriver page skips the sign-in gate there). Unlike site_films.mjs it
 * keeps the app's own clock and animation loop: Street View loads in real time, so the walk is
 * played in real time too, and the page is recorded with Chrome's screencast (every repaint, with
 * its timestamp). DIR gets frames/ and walk.mp4 (30 fps, constant rate) plus a log.
 */
import fs from 'node:fs';
import path from 'node:path';
import { execSync, execFileSync } from 'node:child_process';

const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
const OUT = path.resolve(arg('--out', 'sv-film'));
const URL_ = arg('--url', 'https://dev.chicago.polecat.live/4d/dev/1904/');
const [VW, VH] = arg('--view', '1280x720').split('x').map(Number);
// The page is laid out at --view and drawn at --scale (1.5: a 1280 x 720 layout, as on a laptop, filmed
// at 1920 x 1080), so the Today window is the size a visitor sees it, and sharp.
const SCALE = Number(arg('--scale', '1.5'));
const SETTLE = Number(arg('--settle', '25'));
fs.mkdirSync(path.join(OUT, 'frames'), { recursive: true });
const logf = path.join(OUT, 'log.txt');
const log = (...a) => { const s = `[${new Date().toISOString()}] ${a.join(' ')}`; console.log(s); fs.appendFileSync(logf, s + '\n'); };

let pw;
try { pw = await import('playwright'); } catch {
  const root = execSync('npm root -g', { encoding: 'utf8' }).trim();
  pw = await import(path.join(root, 'playwright', 'index.js'));
}
const { chromium } = pw.chromium ? pw : pw.default;
const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || undefined, headless: !argv.includes('--headed'),
  args: ['--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--enable-zero-copy', ...(process.platform === 'darwin' ? ['--use-angle=metal'] : [])] });
const page = await browser.newPage({ viewport: { width: VW, height: VH }, deviceScaleFactor: SCALE });
page.setDefaultTimeout(900_000);
page.on('pageerror', e => log('pageerror', String(e).slice(0, 200)));
await page.addInitScript(() => {
  localStorage.setItem('chicago4d.detail', 'full');
  localStorage.setItem('chicago4d.entered', '1');
  localStorage.setItem('chicago4d.help.seen', '1');
  localStorage.setItem('chicago4d.tour.done', '1');
  // The one-time hints (js/tour-offer.js HINTS_KEY) count as seen, so none pops over the film
  // ("Interact works what is in reach…" showed for 6 s as the walk passed the saddle horse).
  localStorage.setItem('chicago4d.hintsSeen', JSON.stringify(['jaunt', 'jump', 'reconstructed', 'interact', 'follow']));
  const s = JSON.parse(localStorage.getItem('chicago4d.settings') || '{}');
  s.detail = 'full'; s.quality = 'high';
  localStorage.setItem('chicago4d.settings', JSON.stringify(s));
});
const t0 = Date.now();
if (argv.includes('--small')) await page.addInitScript(() => { window.__svBig = false; });
await page.goto(URL_, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => window.__chicago4d?.ready === true || window.__chicago4d?.error, null, { polling: 1000 });
log(`ready in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
await page.evaluate(async () => {
  const api = window.__chicago4d;
  for (let i = 0; i < 40 && api.welcome?.state !== 'world'; i++) { try { api.welcome?.enter?.('spawn'); } catch {} await new Promise(r => setTimeout(r, 500)); }
  document.exitPointerLock?.();
  for (const b of document.querySelectorAll('button')) if (/got it|dismiss|skip|close tour|not now/i.test(b.textContent ?? '')) b.click();
  api.timeOfDay?.set?.('14:30');
  api.setFly(false);
  api.walker.teleport({ local_e: 1402.6, local_n: -3211, yaw_deg: 265, pitch_deg: 2 });
});
log(`in the town; settling ${SETTLE} s`);
await page.waitForTimeout(SETTLE * 1000);
// Anything still over the view (a tour card, a hint) goes; the app's own interface stays.
// The dev preview's own banner (.github/chicago-4d-dev-preview.mjs) is not part of the app.
await page.addStyleTag({ content: '#look-tag, #__dev, #__devpill { display: none !important; }' });
await page.evaluate(() => { for (const b of document.querySelectorAll('button')) if (/got it|dismiss|skip|not now/i.test(b.textContent ?? '')) b.click(); document.exitPointerLock?.(); });

// ---- record ----------------------------------------------------------------------------
const cdp = await page.context().newCDPSession(page);
const frames = [];
cdp.on('Page.screencastFrame', async (f) => {
  const k = frames.length;
  frames.push(f.metadata.timestamp);
  fs.writeFileSync(path.join(OUT, 'frames', `${String(k).padStart(5, '0')}.jpg`), Buffer.from(f.data, 'base64'));
  try { await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }); } catch {}
});
await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: Math.round(VW * SCALE), maxHeight: Math.round(VH * SCALE), everyNthFrame: 1 });
log('recording');
// The walk, in real time, in the page: a list of beats, each eased; the Today key is pressed
// by the page's own button so the window pops out as a visitor sees it.
const result = await page.evaluate(async () => {
  const api = window.__chicago4d;
  const ease = s => s * s * (3 - 2 * s);
  const yawLerp = (a, b, s) => { const d = ((b - a + 540) % 360) - 180; return (a + d * s + 360) % 360; };
  const bearing = (fe, fn, te, tn) => (Math.atan2(te - fe, tn - fn) * 180 / Math.PI + 360) % 360;
  let at = { e: 1402.6, n: -3211, yaw: 265, pitch: 2 };
  const put = () => api.walker.teleport({ local_e: at.e, local_n: at.n, yaw_deg: at.yaw, pitch_deg: at.pitch });
  const wait = ms => new Promise(r => setTimeout(r, ms));
  async function beat(seconds, to, { evenPace = false } = {}) {
    const from = { ...at }, start = performance.now();
    for (;;) {
      const s = Math.min(1, (performance.now() - start) / (seconds * 1000));
      const k = evenPace ? s : ease(s);
      const look = typeof to.look === 'function' ? to.look : null;
      at = { e: from.e + ((to.e ?? from.e) - from.e) * k, n: from.n + ((to.n ?? from.n) - from.n) * k,
        yaw: look ? from.yaw : yawLerp(from.yaw, to.yaw ?? from.yaw, ease(s)), pitch: from.pitch + ((to.pitch ?? from.pitch) - from.pitch) * ease(s) };
      if (look) at.yaw = yawLerp(from.yaw, look(at), Math.min(1, ease(s) * 2.5));
      put();
      if (s >= 1) break;
      await new Promise(r => requestAnimationFrame(r));
    }
  }
  const notes = [];
  put(); await wait(2500);                                       // the Glessner corner, looking at the house
  document.getElementById('street-today-key')?.click();          // Today: the window pops out
  notes.push('today pressed');
  for (let i = 0; i < 40; i++) { if (document.getElementById('today-view')?.dataset.mode === 'live') break; await wait(250); }
  notes.push(`mode ${document.getElementById('today-view')?.dataset.mode}`);
  await wait(2000);
  // The window made big, as a class would have it on a projector (Kevin's own screenshots).
  if (window.__svBig !== false) document.getElementById('today-expand')?.click();
  await wait(2500);                                              // both views of the corner, side by side
  await beat(4, { yaw: 180 });                                   // turn down Prairie Avenue
  await wait(1200);
  // South along the avenue at a stroll, west of the crown (the saddle horse stands tied at the
  // east kerb), the eye drifting to the Kimball house across the way.
  await beat(2.5, { e: 1400.4, n: -3213 });
  await beat(14, { e: 1399.8, n: -3236, look: (p) => yawLerp(180, bearing(p.e, p.n, 1428, -3222), Math.max(0, Math.min(1, (-3214 - p.n) / 18))) }, { evenPace: true });
  await beat(3, { yaw: bearing(1399.8, -3236, 1428, -3222), pitch: 6 });   // the Kimball house, settled
  await wait(4500);
  await beat(5, { yaw: bearing(1399.8, -3236, 1401, -3196) - 25, pitch: 3 }); // back up the avenue to the corner
  await wait(3500);
  notes.push(`end mode ${document.getElementById('today-view')?.dataset.mode}`, document.getElementById('today-where')?.textContent ?? '');
  return notes;
});
await cdp.send('Page.stopScreencast');
await page.waitForTimeout(500);
log('notes', JSON.stringify(result), `${frames.length} frames`);
await browser.close();

// ---- encode at a constant 30 fps from the screencast's own timestamps --------------------
const list = [];
for (let k = 0; k < frames.length; k++) {
  const d = k + 1 < frames.length ? Math.max(0.001, frames[k + 1] - frames[k]) : 1 / 30;
  list.push(`file 'frames/${String(k).padStart(5, '0')}.jpg'`, `duration ${d.toFixed(4)}`);
}
list.push(`file 'frames/${String(frames.length - 1).padStart(5, '0')}.jpg'`);
fs.writeFileSync(path.join(OUT, 'frames.txt'), list.join('\n'));
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', path.join(OUT, 'frames.txt'),
  '-vf', `fps=30,scale=${Math.round(VW * SCALE)}:${Math.round(VH * SCALE)}:flags=lanczos`, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow',
  '-movflags', '+faststart', path.join(OUT, 'walk.mp4')]);
const span = frames.length > 1 ? frames.at(-1) - frames[0] : 0;
log(`walk.mp4: ${span.toFixed(1)} s, ${frames.length} frames (${(frames.length / Math.max(1, span)).toFixed(1)} fps captured)`);
