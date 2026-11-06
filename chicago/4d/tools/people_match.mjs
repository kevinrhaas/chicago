// T-3417: the paired-still acceptance rig for people. A person is done when a still of them sits
// beside period photographs of someone in the same role and reads as the same kind of picture —
// the buildings' image gate (AGENTS.md rule 11, tools/photo_match.mjs) applied to people.
//
//   node tools/people_match.mjs data/people_match/subjects/<id>.json
//        [--url <walk page> | --published] [--evidence <chicago-evidence clone>] [--out <dir>]
//        [--viewport desktop|phone] [--no-clip]
//
// It boots the real app in the town's own light (not a review render: the person is judged
// in the scene a visitor sees), finds the subject, stops them, and shoots fixed stills:
//   near  3 m from the head,  far  10 m from it,
// each on desktop (1280x800) and phone (390x780), from a camera at a standing person's eye
// height on the ground, at a bearing measured from the subject's own heading, aimed at a point
// a set distance below the head bone. Then, with the clock running, a strip of frames about
// 5 seconds long at the subject's `clip` still, for how the figure moves.
//
// Beside each band it lays the reference set's pictures of that band (data/people_match/
// reference_sets/<set>.json; the files are in kevinrhaas/chicago-evidence and are verified by
// sha256 before anything is shot) and writes:
//   <out>/<still>-<viewport>.jpg          the bare stills
//   <out>/<band>-side-by-side.jpg         the band's pictures | desktop still | phone still
//   <out>/motion-strip.jpg                the clip
//   data/people_match/subjects/<id>.match.json   the match record
// <out> defaults to <evidence>/evidence/people-match-<date>/<subject>/, so the pictures go to
// the evidence repo and only the record goes in this one.
//
// THE MATCH RECORD. Like the buildings' (data/reference_views/README.md): the figure it was shot
// on (`bound`: the transport row's asset, clip and livery hashes), each still's sha256, a
// `verdict` (unreviewed | differs | matches) and a `checklist` answering each item of the plan's
// list (tools/people_match_records.mjs CHECKLIST). A reshoot of the same figure keeps verdict and
// checklist; a reshoot of a changed figure keeps the notes and sets the verdict back to
// unreviewed. tools/test_people_match.mjs holds the records in check.sh.
//
// The default target is the dev preview, so a still shows what is merged. --published shoots a
// local mirror (tools/publish.sh) to judge a branch before it merges.
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { SETS, VIEWPORTS, CHECKLIST, readJSON, checkSet, checkSubject, boundValues } from './people_match_records.mjs';

const root = process.cwd();
const require = createRequire(path.join(root, 'tools/qa.mjs'));
const { chromium } = require('playwright');
const args = process.argv.slice(2);
const opt = (k, d = null) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const flag = k => args.includes(k);
const subjectFile = args.find(a => a.endsWith('.json'));
if (!subjectFile) { console.error('usage: node tools/people_match.mjs data/people_match/subjects/<id>.json [--url URL | --published] [--evidence DIR] [--out DIR] [--viewport desktop|phone] [--no-clip]'); process.exit(2); }

const rel = path.relative(root, path.resolve(subjectFile));
const subject = readJSON(root, rel);
const set = readJSON(root, `${SETS}/${subject.reference_set}.json`);
const problems = [...checkSet(root, set, `${SETS}/${set.id}.json`), ...checkSubject(root, subject, new Map([[set.id, set]]), rel)];
if (problems.length) { for (const p of problems) console.error(p); process.exit(1); }

const sha = buf => crypto.createHash('sha256').update(buf).digest('hex');
const evidence = path.resolve(opt('--evidence', process.env.CHICAGO_EVIDENCE || path.resolve(root, '../../../chicago-evidence')));
const setDir = path.join(evidence, set.evidence.dir);
for (const p of set.pictures) {
  const f = path.join(setDir, p.file);
  if (!fs.existsSync(f)) { console.error(`reference ${p.name}: no ${f} — clone kevinrhaas/chicago-evidence and pass --evidence`); process.exit(1); }
  if (sha(fs.readFileSync(f)) !== p.sha256) { console.error(`reference ${p.name}: ${f} is not the picture the set records (sha256 differs)`); process.exit(1); }
}
const today = new Date().toISOString().slice(0, 10);
const out = path.resolve(opt('--out', path.join(evidence, 'evidence', `people-match-${today}`, subject.id)));
fs.mkdirSync(out, { recursive: true });

// ---- the target -------------------------------------------------------------------------
let server = null, target;
if (flag('--published')) {
  const site = path.resolve(root, '../../site/4d');
  if (!fs.existsSync(path.join(site, 'walk', 'index.html'))) { console.error(`no published mirror at ${site} — run tools/publish.sh first`); process.exit(2); }
  const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
    '.glb': 'model/gltf-binary', '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
    '.wasm': 'application/wasm', '.ktx2': 'image/ktx2', '.geojson': 'application/json', '.woff2': 'font/woff2' };
  server = http.createServer((req, res) => {
    const url = decodeURIComponent(req.url.split('?')[0]);
    let file = path.join(site, url);
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
    if (!file.startsWith(site) || !fs.existsSync(file)) { res.writeHead(404).end(); return; }
    res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  target = `http://127.0.0.1:${server.address().port}/walk/?year=${subject.scene}`;
} else {
  target = opt('--url', `https://chicago.polecat.live/4d/dev/walk/?year=${subject.scene}`);
}
console.log(`people_match: ${subject.id} against ${set.id}, target ${flag('--published') ? 'local published mirror' : target}`);

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const viewports = Object.entries(VIEWPORTS).filter(([vp]) => !opt('--viewport') || opt('--viewport') === vp);
const stills = {}, cameras = {};
let build = null, clipFrames = [], shotBound = null;

for (const [vp, [w, h]] of viewports) {
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1, isMobile: vp === 'phone', hasTouch: vp === 'phone' });
  const pageErrors = [];
  page.on('pageerror', e => pageErrors.push(e.message));
  // Scene detail as a visitor would choose it: Full on desktop; on a phone the lowest tier that
  // draws people at all (a phone boots at Light, which draws none).
  const detail = subject.detail?.[vp] ?? (vp === 'phone' ? 'balanced' : 'full');
  await page.addInitScript(level => {
    let saved = {}; try { saved = JSON.parse(localStorage.getItem('chicago4d.settings') || '{}') ?? {}; } catch { /* none */ }
    localStorage.setItem('chicago4d.settings', JSON.stringify({ ...saved, detail: level }));
    localStorage.setItem('chicago4d.help.seen', '1');
  }, detail);
  const t0 = Date.now(), secs = () => ((Date.now() - t0) / 1000).toFixed(0);
  await page.goto(target, { waitUntil: 'domcontentloaded', timeout: 180_000 });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 400_000 });
  // Free roam closes the welcome; until it does the town's transport does not approach anyone.
  // The button is shown only once the arrival settles, so wait for it as a visitor would.
  await page.locator('#home-roam').click({ timeout: 90_000 }).catch(() => page.evaluate(() => document.getElementById('home-roam')?.click()));
  build ??= await page.evaluate(() => ({ version: window.__chicago4d.version ?? null,
    banner: document.getElementById('gate-build')?.textContent?.trim() || null }));
  console.log(`  ${vp}: ready in ${secs()} s at ${detail} detail (build ${build.banner ?? build.version})`);
  // The figure the stills are of is the target's, not this tree's: read the bound file the page
  // itself loaded, so a record shot on the dev preview from an older checkout binds what was shot.
  shotBound ??= await page.evaluate(async file => {
    const hit = performance.getEntriesByType('resource').map(e => e.name).find(u => u.split('?')[0].endsWith(file));
    return hit ? (await fetch(hit)).json() : null;
  }, subject.bound.file.replace(/^data\//, ''));

  // Find the subject. A driven person is found where Find this person finds them (their route's
  // own reading), approached on foot until their assembly loads, and stopped as an approach
  // stops them: the stills are of a figure at rest on the box, as the photographs are.
  const anchor = await page.evaluate(pid => {
    const a = window.__chicago4d.townTransport?.driverAnchorForPerson(pid);
    return a ? { at: a.at, yaw: a.yaw_rad } : null;
  }, subject.person_id);
  if (!anchor) throw Error(`${subject.person_id}: the town has no driver anchor for them in ${subject.scene} (detail must be Full or Balanced)`);
  await page.evaluate(({ at }) => { const api = window.__chicago4d; api.setFly(true); api.walker.teleport({ local_e: at[0] + 8, local_n: at[1] + 8, yaw_deg: 225, altitude_m: 1.68 }); }, anchor);
  await page.waitForFunction(pid => {
    const tt = window.__chicago4d.townTransport; const d = tt?.driverForPerson(pid);
    if (!d) return false;
    let head = false; tt.group.traverse(o => { if (o.isBone && o.name === 'head') head = true; });
    return head;
  }, subject.person_id, { timeout: 300_000, polling: 1000 });
  await page.evaluate(pid => window.__chicago4d.townTransport.stopPerson(pid), subject.person_id);
  await page.waitForTimeout(4000);
  const figure = await page.evaluate(({ pid, bone }) => {
    const api = window.__chicago4d, tt = api.townTransport, d = tt.driverForPerson(pid);
    let head = null; tt.group.traverse(o => { if (!head && o.isBone && o.name === bone) head = o.getWorldPosition(new o.position.constructor()); });
    const a = tt.driverAnchorForPerson(pid);
    return { state: d.state, head: head && [head.x, head.y, head.z], yaw: a.yaw_rad };
  }, { pid: subject.person_id, bone: subject.aim_bone ?? 'head' });
  if (figure.state !== 'stopped' || !figure.head) throw Error(`${subject.person_id}: could not stop and find the figure (${JSON.stringify(figure)})`);
  // The route's yaw: forward is (sin yaw, -cos yaw) in (east, north), the same reading as
  // town-transport.js driverAnchorForPerson, so the heading is 180 - yaw as a compass bearing.
  const heading = ((180 - figure.yaw * 180 / Math.PI) % 360 + 360) % 360;
  const [hx, hy, hz] = figure.head, headE = hx, headN = -hz;

  // Hide everything but the render surface (as critic_shots.mjs): the stills are of the town.
  await page.addStyleTag({ content: 'body > *:not(#view) { visibility: hidden !important; }' });

  const shoot = async still => {
    const b = (heading + still.bearing_off_heading_deg) * Math.PI / 180;
    const e = headE + Math.sin(b) * still.distance_m, n = headN + Math.cos(b) * still.distance_m;
    const look = ((Math.atan2(headE - e, headN - n) * 180 / Math.PI) + 360) % 360;
    const placed = await page.evaluate(({ e, n, look, eye }) => {
      const api = window.__chicago4d; api.setFly(true);
      api.walker.teleport({ local_e: e, local_n: n, yaw_deg: look, altitude_m: eye, pitch_deg: 0 });
      return { y: api.player.y };
    }, { e, n, look, eye: still.eye_m });
    const pitch = Math.atan2(hy - still.aim_below_head_m - placed.y, still.distance_m) * 180 / Math.PI;
    await page.evaluate(({ e, n, look, eye, pitch }) => window.__chicago4d.walker.teleport({ local_e: e, local_n: n, yaw_deg: look, altitude_m: eye, pitch_deg: pitch }), { e, n, look, eye: still.eye_m, pitch });
    return { e: +e.toFixed(3), n: +n.toFixed(3), eye_y: +placed.y.toFixed(3), yaw_deg: +look.toFixed(2), pitch_deg: +pitch.toFixed(2),
      subject_heading_deg: +heading.toFixed(2), head_enu: [+headE.toFixed(3), +headN.toFixed(3), +hy.toFixed(3)] };
  };
  const settle = () => page.evaluate(async () => { const api = window.__chicago4d; for (let i = 0; i < 8; i++) await api.capture(4); });

  for (const still of subject.stills) {
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    const cam = await shoot(still);
    await page.waitForTimeout(2500); // the near-camera rings (flora, trees, ground reach) rebuild
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    await settle();
    const file = path.join(out, `${still.name}-${vp}.jpg`);
    await page.screenshot({ path: file, type: 'jpeg', quality: 88, timeout: 300_000 });
    // Where the figure stands in the frame: the head bone projected, and a box from just over
    // the hat to the feet, so the sheet can also show the figure cropped to the pictures' scale.
    const box = await page.evaluate(({ head, up, down }) => {
      const api = window.__chicago4d, cam = api.camera, V = cam.position.constructor, el = api.renderer?.domElement ?? document.querySelector('#view canvas');
      cam.updateMatrixWorld(); const r = el.getBoundingClientRect();
      const px = y => { const v = new V(head[0], y, head[2]).project(cam); return [r.left + (v.x + 1) / 2 * r.width, r.top + (1 - v.y) / 2 * r.height]; };
      const top = px(head[1] + up), bottom = px(head[1] - down), h = bottom[1] - top[1], w = h * 0.62;
      return [Math.round(top[0] - w / 2), Math.round(top[1] - 0.06 * h), Math.round(w), Math.round(h * 1.12)];
    }, { head: figure.head, up: 0.35, down: subject.figure_below_head_m ?? 1.6 });
    stills[`${still.name}-${vp}`] = { file: path.relative(evidence, file), sha256: sha(fs.readFileSync(file)), detail, camera: cam, figure_box_px: box };
    cameras[`${still.name}-${vp}`] = cam;
    console.log(`  ${vp}: ${still.name} (${still.distance_m} m) shot at ${secs()} s`);
  }

  if (!flag('--no-clip') && subject.clip.viewport === vp) {
    // The strip is shot on a held clock and the figure is advanced by exactly the interval
    // between frames, in thirtieth-of-a-second steps of its own visual update (what the frame
    // loop calls each frame): under a software rasteriser one unheld frame takes minutes, so a
    // wall-clock strip would sample whatever the renderer's speed allowed, not 5 seconds.
    const still = subject.stills.find(s => s.name === subject.clip.still);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(false));
    await shoot(still);
    await page.waitForTimeout(2500);
    await page.evaluate(() => window.__chicago4d.setAnimationHold(true));
    for (let i = 0; i < subject.clip.frames; i++) {
      await page.evaluate(async ({ pid, dt, steps }) => {
        const api = window.__chicago4d, actor = api.townTransport.driverForPerson(pid);
        if (steps) {
          actor.updateVisual(0, { paused: false, viewer: api.camera.position }); // clears the held frame's reset
          for (let k = 0; k < steps; k++) actor.updateVisual(dt, { paused: false, viewer: api.camera.position });
        }
        for (let k = 0; k < 3; k++) await api.capture(4);
      }, { pid: subject.person_id, dt: 1 / 30, steps: i ? Math.round(subject.clip.interval_s * 30) : 0 });
      clipFrames.push({ t: +(i * subject.clip.interval_s).toFixed(2), jpg: await page.screenshot({ type: 'jpeg', quality: 85, timeout: 300_000 }) });
    }
    console.log(`  ${vp}: ${clipFrames.length}-frame strip over ${clipFrames.at(-1).t} s of the figure's own time`);
  }
  if (pageErrors.length) console.warn(`  ${vp}: page errors: ${pageErrors.join(' | ')}`);
  await page.close();
}

// ---- the sheets -------------------------------------------------------------------------
// A run of one viewport (--viewport) keeps the other's stills from the record, so the sheets
// always pair both — when the figure has not changed since they were shot.
const recFile = rel.replace(/\.json$/, '.match.json');
const prev = fs.existsSync(path.join(root, recFile)) ? readJSON(root, recFile) : null;
const bound = shotBound ? boundValues(root, subject, shotBound) : boundValues(root, subject);
if (!shotBound) console.warn('  the page never loaded the bound file; binding the record to this tree\'s copy');
else if (JSON.stringify(bound) !== JSON.stringify(boundValues(root, subject))) console.warn('  this tree\'s figure differs from the one shot (bring the branch up to the target before committing the record)');
const sameFigure = prev && JSON.stringify(prev.bound) === JSON.stringify(bound);
const allStills = { ...(sameFigure ? prev.stills : {}), ...stills };
const dataUrl = file => `data:image/jpeg;base64,${fs.readFileSync(file).toString('base64')}`;
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const sheetPage = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
const css = `body{margin:0;background:#15171a;color:#e8e6e1;font:14px/1.35 system-ui,sans-serif}
  .sheet{display:inline-block;padding:18px}h1{font-size:18px;margin:0 0 4px}p.sub{margin:0 0 14px;color:#a9a6a0}
  .row{display:flex;gap:14px;align-items:flex-start}figure{margin:0;display:flex;flex-direction:column;gap:6px}
  figure img,figure canvas{height:H;display:block;border:1px solid #333}figcaption{max-width:CAPpx;font-size:12px;color:#c9c5bd}
  .ours figcaption{color:#9fd3ff}.strip img{height:300px}`;
const render = async (html, file, H, cap) => {
  await sheetPage.setContent(`<!doctype html><meta charset=utf-8><style>${css.replace('height:H', `height:${H}px`).replace('CAPpx', `${cap}px`)}</style>${html}`);
  await sheetPage.evaluate(async H => {
    await Promise.all([...document.images].map(i => i.decode()));
    for (const c of document.querySelectorAll('canvas[data-box]')) {
      const img = new Image(); img.src = c.dataset.src; await img.decode();
      const [x, y, w, h] = c.dataset.box.split(',').map(Number);
      c.height = H; c.width = Math.round(H * w / h);
      const g = c.getContext('2d'); g.fillStyle = '#000'; g.fillRect(0, 0, c.width, c.height);
      g.imageSmoothingQuality = 'high'; g.drawImage(img, x, y, w, h, 0, 0, c.width, c.height);
    }
  }, H);
  await (await sheetPage.$('.sheet')).screenshot({ path: file, type: 'jpeg', quality: 86 });
  return path.relative(evidence, file);
};
const sheets = {};
const shotOn = build?.banner ?? build?.version ?? 'unknown build';
for (const still of subject.stills) {
  const refs = set.pictures.filter(p => p.band === still.name);
  const figs = refs.map(p => `<figure><img src="${dataUrl(path.join(setDir, p.file))}"><figcaption>${esc(p.caption)}</figcaption></figure>`);
  for (const vp of Object.keys(VIEWPORTS)) {
    const st = allStills[`${still.name}-${vp}`];
    if (!st || !fs.existsSync(path.join(evidence, st.file))) continue;
    const src = dataUrl(path.join(evidence, st.file));
    figs.push(`<figure class="ours"><img src="${src}"><figcaption>Ours, ${vp} ${VIEWPORTS[vp].join('×')} at ${st.detail} detail, ${still.distance_m} m, ${esc(shotOn)}</figcaption></figure>`);
    if (st.figure_box_px) figs.push(`<figure class="ours"><canvas data-src="${src}" data-box="${st.figure_box_px.join(',')}"></canvas><figcaption>The same ${vp} still, cropped to the figure (not enlarged in the app)</figcaption></figure>`);
  }
  sheets[`${still.name}-side-by-side`] = await render(`<div class="sheet"><h1>${esc(subject.label)}: ${still.distance_m} m beside ${esc(set.label)}</h1>
    <p class="sub">Period pictures on the left (data/people_match/reference_sets/${set.id}.json); our stills in the town's light on the right.</p>
    <div class="row">${figs.join('')}</div></div>`, path.join(out, `${still.name}-side-by-side.jpg`), 640, 420);
}
if (clipFrames.length) {
  const figs = clipFrames.map(f => `<figure><img src="data:image/jpeg;base64,${f.jpg.toString('base64')}"><figcaption>t = ${f.t} s</figcaption></figure>`);
  sheets['motion-strip'] = await render(`<div class="sheet strip"><h1>${esc(subject.label)}: ${subject.clip.frames} frames over about ${(subject.clip.frames - 1) * subject.clip.interval_s} s, ${subject.clip.viewport}, ${subject.clip.still} still</h1>
    <p class="sub">${esc(shotOn)}. Stopped as an approach stops him; what moves is the figure's own life.</p><div class="row">${figs.join('')}</div></div>`,
  path.join(out, 'motion-strip.jpg'), 300, 480);
}
await browser.close();
server?.close();

// ---- the match record -------------------------------------------------------------------
const checklist = Object.fromEntries(Object.entries(CHECKLIST).map(([k, what]) =>
  [k, prev?.checklist?.[k] ?? { what, status: 'open', note: 'not yet compared' }]));
const record = {
  subject: subject.id,
  reference_set: set.id,
  shot: { date: today, target: flag('--published') ? 'local published mirror' : target, build: shotOn,
    out: path.relative(evidence, out), evidence_repo: set.evidence.repo },
  bound,
  stills: allStills,
  sheets: { ...(sameFigure ? prev.sheets : {}), ...sheets },
  verdict: sameFigure ? prev.verdict : 'unreviewed',
  checklist,
  _how: 'verdict is unreviewed | differs | matches, set by whoever laid the stills beside the pictures; each checklist item is {what, status, note} with status open | reads | not shown | within tolerance | owner ruling — open when a visitor would see the figure is not the pictures’ kind of person in that respect. The first figure of each role is the owner’s call (the plan’s "Your call"); later figures of the role are held to the one he approved. A reshoot of a changed figure (bound) sets the verdict back to unreviewed.',
};
fs.writeFileSync(path.join(root, recFile), JSON.stringify(record, null, 2) + '\n');
console.log(`people_match: wrote ${recFile} (verdict ${record.verdict}${prev && !sameFigure ? ', reset: the figure changed' : ''}) and ${Object.keys(sheets).length} sheets under ${out}`);
